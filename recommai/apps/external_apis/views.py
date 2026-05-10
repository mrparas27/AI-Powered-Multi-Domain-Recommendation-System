from datetime import datetime
import json

from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.external_apis.clients import (
    ExternalAPIError,
    GitHubClient,
    ITunesClient,
    JobHunterClient,
    SerpAPIClient,
    SpotifyClient,
    TMDBClient,
    WeatherAPIClient,
    WikipediaMovieClient,
)
from apps.external_apis.models import ImportLog
from apps.jobs.models import Company, Job
from apps.movies.models import Movie
from apps.movies.posters import curated_poster_for
from apps.music.models import Artist, Song


def error_response(exc):
    return JsonResponse({"error": str(exc)}, status=503)


def movie_fallback(query="", warning=""):
    movies = Movie.objects.all()
    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(genres__icontains=query) | Q(overview__icontains=query))
    return {
        "source": "Local fallback",
        "warning": warning,
        "results": [{
            "tmdb_id": movie.tmdb_id,
            "title": movie.title,
            "overview": movie.overview,
            "release_year": movie.release_year,
            "rating": movie.rating,
            "popularity": movie.popularity,
            "poster_url": movie.poster_url,
            "genres": movie.genres,
            "director": movie.director,
            "cast": movie.cast,
            "runtime": movie.runtime,
        } for movie in movies[:20]],
    }


def music_fallback(query="", warning=""):
    songs = Song.objects.select_related("artist")
    if query:
        songs = songs.filter(Q(title__icontains=query) | Q(artist__name__icontains=query) | Q(genres__icontains=query) | Q(mood__icontains=query))
    return {
        "source": "Local fallback",
        "warning": warning,
        "results": [{
            "spotify_id": song.spotify_id,
            "title": song.title,
            "artist": song.artist.name if song.artist else "",
            "album": song.album,
            "duration_ms": song.duration_ms,
            "popularity": song.popularity,
            "preview_url": song.preview_url,
            "image_url": song.image_url,
            "genres": song.genres,
            "mood": song.mood,
        } for song in songs[:20]],
    }


def job_fallback(query="", warning=""):
    jobs = Job.objects.select_related("company")
    if query:
        filters = Q()
        for token in query.replace(",", " ").split():
            if len(token) >= 2:
                filters |= Q(title__icontains=token) | Q(company__name__icontains=token) | Q(skills__icontains=token) | Q(description__icontains=token) | Q(location__icontains=token)
        jobs = jobs.filter(filters) if filters else jobs
    return {
        "source": "Local fallback",
        "warning": warning,
        "results": [{
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company.name if job.company else "",
            "company_logo": job.company.logo_url if job.company else "",
            "location": job.location,
            "description": job.description,
            "requirements": job.requirements,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "job_type": job.job_type,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
            "skills": [skill.strip() for skill in job.skills.split(",") if skill.strip()],
            "apply_url": job.apply_url,
        } for job in jobs[:20]],
    }


def parse_limit(request, default=10, maximum=50):
    try:
        return min(max(int(request.GET.get("limit", str(default))), 1), maximum)
    except ValueError:
        raise ValueError("limit must be an integer.")


def parse_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None


def movie_search(request):
    q = request.GET.get("q", "")
    if not q:
        return JsonResponse({"error": "Provide q."}, status=400)
    try:
        client = TMDBClient()
        results = client.search_movies(q, request.GET.get("year"))[:20]
        results = with_curated_movie_posters(results)
        for item in results:
            save_movie(item)
        return JsonResponse({"source": "TMDB", "query": q, "results": results, "count": len(results)})
    except ExternalAPIError as exc:
        try:
            results = ITunesClient().search_movies(q, limit=20, country=request.GET.get("country", "IN"))
            if not results:
                results = WikipediaMovieClient().search_movies(q, limit=10)
            results = with_curated_movie_posters(results)
            for item in results:
                save_movie(item)
            return JsonResponse({
                "source": "Movie results",
                "query": q,
                "results": results,
                "count": len(results),
            })
        except ExternalAPIError as fallback_exc:
            fallback = movie_fallback(q, f"{exc} {fallback_exc}")
            return JsonResponse({"query": q, **fallback, "count": len(fallback["results"])})


def movie_trending(request):
    try:
        window = request.GET.get("window", "week")
        movies = TMDBClient().trending(window)
        return JsonResponse({"source": "TMDB", "window": window, "movies": movies, "count": len(movies)})
    except ExternalAPIError as exc:
        fallback = movie_fallback("", str(exc))
        return JsonResponse({"window": request.GET.get("window", "week"), "source": fallback["source"], "warning": fallback["warning"], "movies": fallback["results"], "count": len(fallback["results"])})


def movie_details(request, tmdb_id):
    try:
        movie = TMDBClient().details(tmdb_id)
        if request.GET.get("save") == "true":
            save_movie(movie)
        return JsonResponse({"source": "TMDB", "movie": movie})
    except ExternalAPIError as exc:
        fallback = movie_fallback("", str(exc))
        movie = fallback["results"][0] if fallback["results"] else {}
        return JsonResponse({"source": fallback["source"], "warning": fallback["warning"], "movie": movie})


def movie_similar(request, tmdb_id):
    try:
        movies = TMDBClient().similar(tmdb_id)
        return JsonResponse({"source": "TMDB", "tmdb_id": tmdb_id, "similar_movies": movies, "count": len(movies)})
    except ExternalAPIError as exc:
        fallback = movie_fallback("", str(exc))
        return JsonResponse({"source": fallback["source"], "warning": fallback["warning"], "tmdb_id": tmdb_id, "similar_movies": fallback["results"], "count": len(fallback["results"])})


def music_search(request):
    try:
        q = request.GET.get("q", "")
        if not q:
            return JsonResponse({"error": "Provide q."}, status=400)
        results = SpotifyClient().search_tracks(q, parse_limit(request), market=request.GET.get("market", "IN"))
        for item in results:
            save_song(item)
        return JsonResponse({"source": "Spotify", "query": q, "results": results, "count": len(results)})
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except ExternalAPIError as exc:
        try:
            results = ITunesClient().search_tracks(q, parse_limit(request), country=request.GET.get("market", "IN"))
            for item in results:
                save_song(item)
            return JsonResponse({"source": "iTunes", "warning": str(exc), "query": q, "results": results, "count": len(results)})
        except ExternalAPIError as fallback_exc:
            fallback = music_fallback(q, f"{exc} {fallback_exc}")
            return JsonResponse({"query": q, **fallback, "count": len(fallback["results"])})


def music_trending(request):
    try:
        country = request.GET.get("country", "US")
        tracks = SpotifyClient().trending_tracks(country, parse_limit(request))
        return JsonResponse({"source": "Spotify", "country": country, "tracks": tracks, "count": len(tracks)})
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except ExternalAPIError as exc:
        fallback = music_fallback("", str(exc))
        return JsonResponse({"source": fallback["source"], "warning": fallback["warning"], "country": request.GET.get("country", "US"), "tracks": fallback["results"], "count": len(fallback["results"])})


def artist_search(request):
    try:
        q = request.GET.get("q", "")
        if not q:
            return JsonResponse({"error": "Provide q."}, status=400)
        results = SpotifyClient().search_artists(q, parse_limit(request))
        return JsonResponse({"source": "Spotify", "query": q, "results": results, "count": len(results)})
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except ExternalAPIError as exc:
        artists = Artist.objects.filter(Q(name__icontains=q) | Q(genres__icontains=q))[:20]
        results = [{
            "spotify_id": artist.spotify_id,
            "name": artist.name,
            "genres": artist.genres,
            "popularity": artist.popularity,
            "image_url": artist.image_url,
            "followers": artist.followers,
        } for artist in artists]
        return JsonResponse({"source": "Local fallback", "warning": str(exc), "query": q, "results": results, "count": len(results)})


def track_details(request, spotify_id):
    try:
        track = SpotifyClient().track_details(spotify_id)
        if request.GET.get("save") == "true":
            save_song(track)
        return JsonResponse({"source": "Spotify", "track": track})
    except ExternalAPIError as exc:
        fallback = music_fallback("", str(exc))
        track = fallback["results"][0] if fallback["results"] else {}
        return JsonResponse({"source": fallback["source"], "warning": fallback["warning"], "track": track})


def job_search(request):
    q = request.GET.get("q", "")
    location = request.GET.get("location", "")
    try:
        if not q:
            return JsonResponse({"error": "Provide q."}, status=400)
        results = JobHunterClient().search_jobs(q, location, request.GET.get("type", ""))
        for item in results:
            save_job(item)
        return JsonResponse({"source": "JobHunter", "query": q, "results": results, "count": len(results)})
    except ExternalAPIError as exc:
        try:
            results = SerpAPIClient().search_jobs(q, location, limit=20)
            for item in results:
                save_job(item)
            return JsonResponse({"source": "SerpAPI Jobs", "warning": str(exc), "query": q, "results": results, "count": len(results)})
        except ExternalAPIError as fallback_exc:
            fallback = job_fallback(q, f"{exc} {fallback_exc}")
            return JsonResponse({"query": q, **fallback, "count": len(fallback["results"])})


def job_details(request, job_id):
    try:
        job = JobHunterClient().job_details(job_id)
        if request.GET.get("save") == "true":
            save_job(job)
        return JsonResponse({"source": "JobHunter", "job": job})
    except ExternalAPIError as exc:
        fallback = job_fallback("", str(exc))
        job = fallback["results"][0] if fallback["results"] else {}
        return JsonResponse({"source": fallback["source"], "warning": fallback["warning"], "job": job})


def github_repositories(request):
    try:
        q = request.GET.get("q", "machine learning django")
        results = GitHubClient().search_repositories(q, parse_limit(request))
        return JsonResponse({"source": "GitHub", "query": q, "results": results, "count": len(results)})
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except ExternalAPIError as exc:
        return JsonResponse({"source": "Local fallback", "warning": str(exc), "query": q, "results": [], "count": 0})


def company_search(request):
    try:
        q = request.GET.get("q", "")
        if not q:
            return JsonResponse({"error": "Provide q."}, status=400)
        results = JobHunterClient().search_companies(q)
        return JsonResponse({"source": "JobHunter", "query": q, "results": results, "count": len(results)})
    except ExternalAPIError as exc:
        companies = Company.objects.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q))[:20]
        results = [{"name": company.name, "website": company.website, "logo_url": company.logo_url, "description": company.description, "location": company.location} for company in companies]
        return JsonResponse({"source": "Local fallback", "warning": str(exc), "query": q, "results": results, "count": len(results)})


def web_search(request):
    try:
        q = request.GET.get("q", "")
        if not q:
            return JsonResponse({"error": "Provide q."}, status=400)
        results = SerpAPIClient().search(q, parse_limit(request, maximum=20))
        return JsonResponse({"source": "SerpAPI", "query": q, "results": results, "count": len(results)})
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except ExternalAPIError as exc:
        return JsonResponse({"source": "Local fallback", "warning": str(exc), "query": q, "results": [], "count": 0})


def weather_current(request):
    try:
        location = request.GET.get("location", "")
        if not location:
            return JsonResponse({"error": "Provide location."}, status=400)
        weather = WeatherAPIClient().current(location)
        return JsonResponse({"source": "WeatherAPI", "weather": weather})
    except ExternalAPIError as exc:
        return JsonResponse({
            "source": "Local fallback",
            "warning": str(exc),
            "weather": {
                "location": location,
                "condition": "Unavailable",
                "temperature_c": None,
                "humidity": None,
                "wind_kph": None,
            },
        })


def provider_status(request):
    providers = [
        ("TMDB", "TMDB_API_KEY"),
        ("Spotify ID", "SPOTIFY_CLIENT_ID"),
        ("Spotify Secret", "SPOTIFY_CLIENT_SECRET"),
        ("JobHunter", "JOBHUNTER_API_KEY"),
        ("GitHub", "GITHUB_TOKEN"),
        ("SerpAPI", "SERPAPI_API_KEY"),
        ("WeatherAPI", "WEATHER_API_KEY"),
    ]
    return JsonResponse({
        "providers": [{"name": name, "configured": bool(settings.EXTERNAL_APIS.get(key))} for name, key in providers],
        "fallback": "Local seed data is used automatically if a provider is unavailable.",
    })


@csrf_exempt
@require_POST
def import_movies(request):
    body = parse_body(request)
    if body is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    query = body.get("query", "popular")
    errors = []
    imported = 0
    try:
        for item in TMDBClient().search_movies(query)[:20]:
            save_movie(item)
            imported += 1
    except ExternalAPIError as exc:
        errors.append(str(exc))
    ImportLog.objects.create(provider="TMDB", domain="movies", query=query, imported_count=imported, errors=errors)
    return JsonResponse({"imported": imported, "errors": errors})


@csrf_exempt
@require_POST
def import_songs(request):
    body = parse_body(request)
    if body is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    query = body.get("query", "popular")
    errors = []
    imported = 0
    try:
        for item in SpotifyClient().search_tracks(query, 20):
            save_song(item)
            imported += 1
    except ExternalAPIError as exc:
        errors.append(str(exc))
    ImportLog.objects.create(provider="Spotify", domain="music", query=query, imported_count=imported, errors=errors)
    return JsonResponse({"imported": imported, "errors": errors})


@csrf_exempt
@require_POST
def import_jobs(request):
    body = parse_body(request)
    if body is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)
    query = body.get("query", "python")
    errors = []
    imported = 0
    try:
        for item in JobHunterClient().search_jobs(query, body.get("location", ""), body.get("type", ""))[:20]:
            save_job(item)
            imported += 1
    except ExternalAPIError as exc:
        errors.append(str(exc))
    ImportLog.objects.create(provider="JobHunter", domain="jobs", query=query, imported_count=imported, errors=errors)
    return JsonResponse({"imported": imported, "errors": errors})


def save_movie(data):
    title = data.get("title", "").strip()
    if not title:
        return
    defaults = {
            "title": title,
            "overview": data.get("overview", ""),
            "genres": data.get("genres", ""),
            "cast": data.get("cast", ""),
            "director": data.get("director", ""),
            "release_year": data.get("release_year"),
            "runtime": data.get("runtime"),
            "rating": data.get("rating") or 0,
            "popularity": data.get("popularity") or 0,
            "poster_url": data.get("poster_url", "") or curated_poster_for(title),
        }
    tmdb_id = data.get("tmdb_id")
    title_matches = list(Movie.objects.filter(title__iexact=title))
    if title_matches:
        for movie in title_matches:
            if tmdb_id and not Movie.objects.exclude(id=movie.id).filter(tmdb_id=tmdb_id).exists():
                movie.tmdb_id = tmdb_id
            for key, value in defaults.items():
                if value not in ("", None, 0) or key in {"rating", "popularity"}:
                    setattr(movie, key, value)
            movie.save()
        return
    movie = Movie.objects.filter(tmdb_id=tmdb_id).first() if tmdb_id else None
    if movie:
        for key, value in defaults.items():
            if value not in ("", None, 0) or key in {"rating", "popularity"}:
                setattr(movie, key, value)
        movie.save()
        return
    Movie.objects.create(tmdb_id=tmdb_id, **defaults)


def with_curated_movie_posters(results):
    for item in results:
        if not item.get("poster_url"):
            item["poster_url"] = curated_poster_for(item.get("title", ""))
    return results


def save_song(data):
    if not data.get("spotify_id"):
        return
    artist_name = data.get("artist") or "Unknown Artist"
    artist = Artist.objects.filter(name=artist_name).first()
    if not artist:
        artist = Artist.objects.create(name=artist_name, genres=data.get("genres", ""))
    Song.objects.update_or_create(
        spotify_id=data.get("spotify_id"),
        defaults={
            "title": data.get("title", ""),
            "artist": artist,
            "album": data.get("album", ""),
            "genres": data.get("genres", ""),
            "mood": data.get("mood", ""),
            "duration_ms": data.get("duration_ms") or 0,
            "popularity": data.get("popularity") or 0,
            "preview_url": data.get("preview_url", ""),
            "image_url": data.get("image_url", ""),
        },
    )


def save_job(data):
    if not data.get("job_id"):
        return
    company, _ = Company.objects.update_or_create(
        name=data.get("company") or "Unknown Company",
        defaults={
            "logo_url": data.get("company_logo", ""),
            "location": data.get("location", ""),
        },
    )
    posted_at = None
    if data.get("posted_at"):
        try:
            posted_at = datetime.fromisoformat(data["posted_at"][:10]).date()
        except ValueError:
            posted_at = None
    Job.objects.update_or_create(
        job_id=data.get("job_id") or None,
        defaults={
            "title": data.get("title", ""),
            "company": company,
            "location": data.get("location", ""),
            "description": data.get("description", ""),
            "requirements": str(data.get("requirements", "")),
            "skills": ", ".join(data.get("skills") or []),
            "salary_min": data.get("salary_min"),
            "salary_max": data.get("salary_max"),
            "job_type": data.get("job_type", ""),
            "apply_url": data.get("apply_url", ""),
            "posted_at": posted_at,
        },
    )
