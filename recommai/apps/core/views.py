from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.core.serializers import job_dict, movie_dict, song_dict
from apps.external_apis.clients import ExternalAPIError, ITunesClient, TMDBClient, WikipediaMovieClient
from apps.jobs.models import Job
from apps.movies.models import Movie
from apps.movies.posters import curated_poster_for
from apps.music.models import Song
from apps.recommendations.engine import rank_items, tokenize
from apps.recommendations.models import RecommendationEvent

KNOWN_SKILLS = [
    "python", "django", "fastapi", "postgresql", "sql", "rest", "api", "react", "typescript",
    "docker", "aws", "kubernetes", "terraform", "nlp", "scikit-learn", "pandas",
    "redis", "airflow", "ci/cd", "data modeling", "etl", "mlops", "machine learning",
    "deep learning", "llm", "rag", "langchain", "java", "spring", "node", "express",
    "mongodb", "mysql", "power bi", "tableau", "spark", "hadoop", "azure", "gcp",
]

MOOD_TARGETS = {
    "energetic": {"energy": 0.82, "danceability": 0.72, "valence": 0.68},
    "calm": {"energy": 0.25, "danceability": 0.35, "valence": 0.52},
    "romantic": {"energy": 0.45, "danceability": 0.55, "valence": 0.62},
    "focus": {"energy": 0.35, "danceability": 0.30, "valence": 0.45},
    "party": {"energy": 0.88, "danceability": 0.84, "valence": 0.74},
    "sad": {"energy": 0.28, "danceability": 0.30, "valence": 0.22},
    "uplifting": {"energy": 0.70, "danceability": 0.65, "valence": 0.78},
}

ROLE_BLUEPRINTS = {
    "AI Full Stack Engineer": {"python", "django", "react", "api", "nlp"},
    "Generative AI Engineer": {"python", "llm", "rag", "langchain", "machine learning"},
    "Machine Learning Engineer": {"python", "machine learning", "scikit-learn", "pandas", "mlops"},
    "Django Backend Developer": {"python", "django", "postgresql", "redis", "docker"},
    "React Frontend Engineer": {"react", "typescript", "api"},
    "Data Analyst": {"sql", "python", "power bi", "tableau", "pandas"},
    "Cloud DevOps Engineer": {"aws", "docker", "kubernetes", "terraform", "ci/cd"},
}


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


@login_required
def dashboard(request):
    recent_events = RecommendationEvent.objects.filter(user=request.user)[:10]
    return render(request, "core/dashboard.html", {
        "user_profile": getattr(request.user, "profile", None),
        "movie_count": Movie.objects.count(),
        "song_count": Song.objects.count(),
        "job_count": Job.objects.count(),
        "movies": Movie.objects.all()[:6],
        "songs": Song.objects.select_related("artist")[:6],
        "jobs": Job.objects.select_related("company")[:6],
        "recent_events": recent_events,
    })


@login_required
def movies_page(request):
    q = request.GET.get("q", "")
    selected_id = request.GET.get("movie_id")
    movie_title = request.GET.get("movie_title", "").strip()
    page = max(int(request.GET.get("page", "1")), 1)
    page_size = 24
    movies = Movie.objects.all()
    if q:
        movies = movies.filter(Q(title__icontains=q) | Q(genres__icontains=q) | Q(overview__icontains=q))
    total = movies.count()
    start = (page - 1) * page_size
    end = start + page_size
    similar_movies = []
    selected_movie = None
    if movie_title:
        selected_movie = (
            Movie.objects.filter(title__iexact=movie_title).first()
            or Movie.objects.filter(title__icontains=movie_title).first()
        )
    if selected_id and not selected_movie:
        selected_movie = Movie.objects.filter(id=selected_id).first()
    if selected_movie:
        selected_movie = enrich_movie_from_provider(selected_movie)
        ranked = rank_items(selected_movie.recommendation_text, Movie.objects.exclude(id=selected_movie.id), lambda m: m.recommendation_text, limit=8)
        similar_movies = [{"score": row["score"], "movie": apply_curated_movie_art(row["item"])} for row in ranked]
    return render(request, "core/movies.html", {
        "movies": movies[start:end],
        "query": q,
        "movie_title": movie_title,
        "page": page,
        "has_prev": page > 1,
        "has_next": end < total,
        "selected_movie": selected_movie,
        "similar_movies": similar_movies,
        "all_movies": Movie.objects.only("id", "title").order_by("title")[:500],
    })


@login_required
def music_page(request):
    q = request.GET.get("q", "")
    mood = request.GET.get("mood", "")
    page = max(int(request.GET.get("page", "1")), 1)
    page_size = 24
    songs = Song.objects.select_related("artist")
    if q:
        songs = songs.filter(Q(title__icontains=q) | Q(genres__icontains=q) | Q(artist__name__icontains=q) | Q(mood__icontains=q))
    total = songs.count()
    start = (page - 1) * page_size
    end = start + page_size
    mood_recommendations = recommend_songs_by_mood(mood) if mood else []
    return render(request, "core/music.html", {
        "songs": songs[start:end],
        "query": q,
        "page": page,
        "has_prev": page > 1,
        "has_next": end < total,
        "mood": mood,
        "mood_recommendations": mood_recommendations,
    })


@login_required
def jobs_page(request):
    q = request.GET.get("q", "")
    page = max(int(request.GET.get("page", "1")), 1)
    page_size = 24
    jobs = Job.objects.select_related("company")
    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(skills__icontains=q) | Q(description__icontains=q))
    total = jobs.count()
    start = (page - 1) * page_size
    end = start + page_size
    resume_text = request.POST.get("resume_text", "").strip() if request.method == "POST" else ""
    resume_file_error = ""
    resume_matches = []
    related_jobs = []
    extracted_skills = []
    suggested_roles = []
    if request.method == "POST" and not resume_text and request.FILES.get("resume_file"):
        resume_text, resume_file_error = extract_text_from_uploaded_resume(request.FILES["resume_file"])
    if resume_text:
        extracted_skills = extract_skills_from_resume(resume_text)
        suggested_roles = suggest_roles_from_skills(extracted_skills)
        query_text = " ".join(extracted_skills) if extracted_skills else resume_text
        ranked = rank_items(query_text, Job.objects.select_related("company"), lambda j: j.recommendation_text, limit=8)
        resume_matches = [{"score": row["score"], "job": row["item"]} for row in ranked]
        if resume_matches:
            base_job = resume_matches[0]["job"]
            near = rank_items(base_job.recommendation_text, Job.objects.exclude(id=base_job.id).select_related("company"), lambda j: j.recommendation_text, limit=6)
            related_jobs = [{"score": row["score"], "job": row["item"]} for row in near]
    return render(request, "core/jobs.html", {
        "jobs": jobs[start:end],
        "query": q,
        "page": page,
        "has_prev": page > 1,
        "has_next": end < total,
        "resume_text": resume_text,
        "resume_file_error": resume_file_error,
        "resume_matches": resume_matches,
        "related_jobs": related_jobs,
        "extracted_skills": extracted_skills,
        "suggested_roles": suggested_roles,
    })


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


def health(request):
    return JsonResponse({"status": "ok", "service": "RecommAI"})


def local_movies(request):
    q = request.GET.get("q", "")
    movies = Movie.objects.all()
    if q:
        movies = movies.filter(Q(title__icontains=q) | Q(genres__icontains=q) | Q(overview__icontains=q))
    return JsonResponse({"results": [movie_dict(movie) for movie in movies[:50]], "count": movies.count()})


def local_music(request):
    q = request.GET.get("q", "")
    songs = Song.objects.select_related("artist")
    if q:
        songs = songs.filter(Q(title__icontains=q) | Q(genres__icontains=q) | Q(artist__name__icontains=q))
    return JsonResponse({"results": [song_dict(song) for song in songs[:50]], "count": songs.count()})


def local_jobs(request):
    q = request.GET.get("q", "")
    jobs = Job.objects.select_related("company")
    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(skills__icontains=q) | Q(description__icontains=q))
    return JsonResponse({"results": [job_dict(job) for job in jobs[:50]], "count": jobs.count()})


def recommend(request):
    domain = request.GET.get("domain", "movies")
    q = request.GET.get("q", "")
    try:
        limit = min(max(int(request.GET.get("limit", "10")), 1), 25)
    except ValueError:
        return JsonResponse({"error": "limit must be an integer."}, status=400)
    if not q:
        return JsonResponse({"error": "Provide a q query parameter."}, status=400)

    if domain == "music":
        ranked = rank_items(q, Song.objects.select_related("artist"), lambda s: s.recommendation_text, limit)
        results = [{"score": r["score"], **song_dict(r["item"])} for r in ranked]
    elif domain == "jobs":
        ranked = rank_items(q, Job.objects.select_related("company"), lambda j: j.recommendation_text, limit)
        results = [{"score": r["score"], **job_dict(r["item"])} for r in ranked]
    else:
        domain = "movies"
        ranked = rank_items(q, Movie.objects.all(), lambda m: m.recommendation_text, limit)
        results = [{"score": r["score"], **movie_dict(r["item"])} for r in ranked]

    RecommendationEvent.objects.create(
        user=request.user if request.user.is_authenticated else None,
        domain=domain,
        query=q,
        result_count=len(results),
        explanation="Content similarity using tokenized cosine scoring.",
    )
    return JsonResponse({"domain": domain, "query": q, "results": results, "count": len(results)})


def extract_skills_from_resume(resume_text):
    tokens = set(tokenize(resume_text))
    found = []
    for skill in KNOWN_SKILLS:
        skill_tokens = set(tokenize(skill))
        if skill_tokens and skill_tokens.issubset(tokens):
            found.append(skill)
    return found


def suggest_roles_from_skills(skills):
    skill_set = set(skills)
    scored = []
    for role, required in ROLE_BLUEPRINTS.items():
        overlap = skill_set & required
        if overlap:
            scored.append({
                "title": role,
                "score": round(len(overlap) / len(required), 2),
                "matched": sorted(overlap),
                "missing": sorted(required - skill_set)[:4],
            })
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:5]


def extract_text_from_uploaded_resume(uploaded_file):
    name = (uploaded_file.name or "").lower()
    data = uploaded_file.read()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore"), ""
    if name.endswith(".pdf"):
        text = extract_pdf_text(data)
        if text:
            return text, ""
        raw_text = extract_text_from_binary(data)
        if raw_text:
            return raw_text, "PDF text layer was weak, so RecommAI used a fallback byte-level text extraction."
        return "", "This PDF looks scanned or image-only, so text skills could not be read. Upload a text-based PDF/DOCX or paste the resume text."
    if name.endswith(".docx"):
        try:
            import io
            from docx import Document

            document = Document(io.BytesIO(data))
            text = " ".join(p.text for p in document.paragraphs)
            return text.strip(), ""
        except Exception:
            return "", "Could not parse DOCX. Paste resume text or upload TXT."
    return "", "Unsupported file type. Use TXT, PDF, or DOCX."


def extract_pdf_text(data):
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        return compact_resume_text(text)
    except Exception:
        return ""


def extract_text_from_binary(data):
    decoded = data.decode("latin-1", errors="ignore")
    import re

    chunks = re.findall(r"[A-Za-z][A-Za-z0-9+#./@,() _-]{2,}", decoded)
    text = " ".join(chunk.strip() for chunk in chunks)
    return compact_resume_text(text)


def compact_resume_text(text):
    import re

    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) >= 20 else ""


def enrich_movie_from_provider(movie):
    if movie.poster_url:
        return movie
    curated = curated_poster_for(movie.title)
    if curated:
        movie.poster_url = curated
        movie.save(update_fields=["poster_url", "updated_at"])
        return movie
    best = {}
    try:
        matches = ITunesClient().search_movies(movie.title, limit=1)
        best = matches[0] if matches else {}
    except ExternalAPIError:
        best = {}
    if not best:
        try:
            matches = WikipediaMovieClient().search_movies(movie.title, limit=1)
            best = matches[0] if matches else {}
        except ExternalAPIError:
            best = {}
    if not best:
        try:
            client = TMDBClient()
            matches = client.search_movies(movie.title, movie.release_year)
            best = client.enrich_search_result(matches[0]) if matches else {}
        except ExternalAPIError:
            best = {}
    if not best:
        return movie
    try:
        tmdb_id = best.get("tmdb_id")
        if tmdb_id and Movie.objects.exclude(id=movie.id).filter(tmdb_id=tmdb_id).exists():
            movie.tmdb_id = movie.tmdb_id
        else:
            movie.tmdb_id = tmdb_id or movie.tmdb_id
        movie.poster_url = best.get("poster_url") or movie.poster_url
        movie.overview = best.get("overview") or movie.overview
        movie.genres = best.get("genres") or movie.genres
        movie.cast = best.get("cast") or movie.cast
        movie.director = best.get("director") or movie.director
        movie.runtime = best.get("runtime") or movie.runtime
        movie.rating = best.get("rating") or movie.rating
        movie.popularity = best.get("popularity") or movie.popularity
        movie.save(update_fields=["tmdb_id", "poster_url", "overview", "genres", "cast", "director", "runtime", "rating", "popularity", "updated_at"])
    except Exception:
        return movie
    return movie


def apply_curated_movie_art(movie):
    if not movie.poster_url:
        movie.poster_url = curated_poster_for(movie.title)
    return movie

def recommend_songs_by_mood(mood, limit=12):
    mood_norm = (mood or "").strip().lower()
    target = None
    for key, value in MOOD_TARGETS.items():
        if key in mood_norm:
            target = value
            break
    songs = list(Song.objects.select_related("artist").all()[:5000])
    if not songs:
        return []
    if not target:
        return Song.objects.select_related("artist").filter(
            Q(mood__icontains=mood_norm) | Q(genres__icontains=mood_norm) | Q(title__icontains=mood_norm)
        ).order_by("-popularity")[:limit]

    def score(song):
        # Weighted distance over audio-feel fields + slight popularity boost.
        distance = (
            abs(song.energy - target["energy"]) * 0.45
            + abs(song.danceability - target["danceability"]) * 0.35
            + abs(song.valence - target["valence"]) * 0.20
        )
        pop_bonus = min(song.popularity, 100) / 1000
        return distance - pop_bonus

    ranked = sorted(songs, key=score)
    return ranked[:limit]


def api_similar_movies(request, movie_id):
    movie = Movie.objects.filter(id=movie_id).first()
    if not movie:
        return JsonResponse({"error": "movie not found"}, status=404)
    ranked = rank_items(movie.recommendation_text, Movie.objects.exclude(id=movie.id), lambda m: m.recommendation_text, limit=10)
    results = [{"score": row["score"], **movie_dict(row["item"])} for row in ranked]
    return JsonResponse({"movie": movie_dict(movie), "similar": results, "count": len(results)})


def api_music_by_mood(request):
    mood = request.GET.get("mood", "").strip()
    if not mood:
        return JsonResponse({"error": "Provide mood query parameter."}, status=400)
    songs = recommend_songs_by_mood(mood, limit=25)
    return JsonResponse({"mood": mood, "results": [song_dict(song) for song in songs], "count": len(songs)})


def api_resume_job_match(request):
    resume_text = request.GET.get("resume", "").strip()
    if not resume_text:
        return JsonResponse({"error": "Provide resume query parameter."}, status=400)
    skills = extract_skills_from_resume(resume_text)
    query_text = " ".join(skills) if skills else resume_text
    ranked = rank_items(query_text, Job.objects.select_related("company"), lambda j: j.recommendation_text, limit=10)
    results = [{"score": row["score"], **job_dict(row["item"])} for row in ranked]
    similar = []
    if ranked:
        base = ranked[0]["item"]
        near = rank_items(base.recommendation_text, Job.objects.exclude(id=base.id).select_related("company"), lambda j: j.recommendation_text, limit=6)
        similar = [{"score": row["score"], **job_dict(row["item"])} for row in near]
    return JsonResponse({"skills": skills, "matches": results, "similar_jobs": similar, "count": len(results)})
