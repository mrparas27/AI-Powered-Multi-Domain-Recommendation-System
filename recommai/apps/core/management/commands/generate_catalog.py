import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.jobs.models import Company, Job
from apps.movies.models import Movie
from apps.music.models import Artist, Song


class Command(BaseCommand):
    help = "Generate large local datasets for movies, music, and jobs."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10000, help="Records per domain (default: 10000).")
        parser.add_argument("--reset", action="store_true", help="Delete existing records before generation.")

    @staticmethod
    def chunked_create(model, objects, batch_size=1000):
        for idx in range(0, len(objects), batch_size):
            model.objects.bulk_create(objects[idx:idx + batch_size], ignore_conflicts=True)

    def handle(self, *args, **options):
        count = max(options["count"], 100)
        reset = options["reset"]
        random.seed(20260510)

        if reset:
            self.stdout.write("Resetting existing records...")
            Song.objects.all().delete()
            Artist.objects.all().delete()
            Job.objects.all().delete()
            Company.objects.all().delete()
            Movie.objects.all().delete()

        if Movie.objects.count() >= count and Song.objects.count() >= count and Job.objects.count() >= count:
            self.seed_curated_movies()
            self.seed_curated_music()
            self.seed_curated_jobs()
            self.stdout.write(self.style.SUCCESS("Catalog already has requested scale."))
            return

        genres = ["Action", "Drama", "Thriller", "Sci-Fi", "Romance", "Comedy", "Mystery", "Adventure", "Fantasy", "Crime"]
        moods = ["energetic", "calm", "dramatic", "uplifting", "dark", "focused", "romantic", "nostalgic"]
        locations = ["Remote", "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Pune", "Chennai", "Kolkata", "Noida", "Gurgaon"]
        companies = ["Nova Systems", "Pulse Analytics", "Aster Labs", "BlueOrbit", "Maple Tech", "Cipher Stack", "VertexOps", "LumenAI", "DriftWorks", "Quantum Forge"]
        roles = ["Python Developer", "Data Engineer", "ML Engineer", "Backend Engineer", "Frontend Engineer", "DevOps Engineer", "Product Analyst", "Platform Engineer", "AI Engineer", "Django Engineer"]
        skill_sets = [
            "Python, Django, PostgreSQL, REST",
            "Python, FastAPI, Redis, Docker",
            "React, TypeScript, APIs, UX",
            "NLP, scikit-learn, pandas, SQL",
            "AWS, CI/CD, Terraform, Kubernetes",
            "Data Modeling, SQL, ETL, Airflow",
        ]

        self.stdout.write(f"Generating {count} movies...")
        movie_objects = []
        for idx in range(1, count + 1):
            g1 = genres[idx % len(genres)]
            g2 = genres[(idx * 3) % len(genres)]
            title = f"{g1} Story {idx:05d}"
            movie_objects.append(Movie(
                tmdb_id=500000 + idx,
                title=title,
                overview=f"{title} follows a layered narrative around ambition, conflict, and redemption.",
                genres=f"{g1}, {g2}",
                cast=f"Actor {idx%500}, Actor {(idx+7)%500}, Actor {(idx+14)%500}",
                director=f"Director {idx%200}",
                release_year=1980 + (idx % 45),
                runtime=85 + (idx % 60),
                rating=round(5.5 + (idx % 45) / 10, 1),
                popularity=round(20 + (idx % 800) / 10, 1),
                poster_url="",
            ))
        self.chunked_create(Movie, movie_objects)
        self.seed_curated_movies()

        artist_target = max(2000, count // 4)
        self.stdout.write(f"Generating {artist_target} artists...")
        artist_objects = []
        for idx in range(1, artist_target + 1):
            genre = genres[idx % len(genres)]
            artist_objects.append(Artist(
                spotify_id=f"artist_{idx:05d}",
                name=f"Artist {idx:05d}",
                genres=genre,
                popularity=30 + (idx % 70),
                image_url="",
                followers=1000 + idx * 17,
            ))
        self.chunked_create(Artist, artist_objects)

        artist_ids = list(Artist.objects.values_list("id", flat=True)[:artist_target])
        self.stdout.write(f"Generating {count} songs...")
        song_objects = []
        for idx in range(1, count + 1):
            mood = moods[idx % len(moods)]
            genre = genres[(idx * 5) % len(genres)]
            song_objects.append(Song(
                spotify_id=f"track_{idx:06d}",
                title=f"{mood.title()} Track {idx:05d}",
                artist_id=artist_ids[idx % len(artist_ids)],
                album=f"{genre} Album {(idx % 900) + 1}",
                genres=genre,
                mood=mood,
                duration_ms=120000 + (idx % 240000),
                popularity=40 + (idx % 60),
                tempo=80 + (idx % 110),
                energy=round((idx % 100) / 100, 2),
                danceability=round(((idx * 3) % 100) / 100, 2),
                valence=round(((idx * 7) % 100) / 100, 2),
                acousticness=round(((idx * 11) % 100) / 100, 2),
                preview_url="",
                image_url="",
            ))
        self.chunked_create(Song, song_objects)
        self.seed_curated_music()

        company_target = max(3000, count // 3)
        self.stdout.write(f"Generating {company_target} companies...")
        company_objects = []
        for idx in range(1, company_target + 1):
            company_objects.append(Company(
                name=f"{companies[idx % len(companies)]} {idx:04d}",
                website="",
                logo_url="",
                description="Product and engineering focused organization.",
                location=locations[idx % len(locations)],
            ))
        self.chunked_create(Company, company_objects)

        company_ids = list(Company.objects.values_list("id", flat=True)[:company_target])
        self.stdout.write(f"Generating {count} jobs...")
        job_objects = []
        base_date = date.today()
        for idx in range(1, count + 1):
            role = roles[idx % len(roles)]
            skills = skill_sets[idx % len(skill_sets)]
            job_objects.append(Job(
                job_id=f"job_{idx:06d}",
                title=f"{role} {idx:05d}",
                company_id=company_ids[idx % len(company_ids)],
                location=locations[(idx * 2) % len(locations)],
                description=f"Work on scalable systems and product delivery for {role.lower()} responsibilities.",
                requirements=f"2+ years relevant experience. Skills: {skills}.",
                skills=skills,
                salary_min=40000 + (idx % 120) * 1000,
                salary_max=70000 + (idx % 160) * 1000,
                job_type=["full-time", "contract", "hybrid"][idx % 3],
                apply_url="",
                posted_at=base_date - timedelta(days=idx % 120),
            ))
        self.chunked_create(Job, job_objects)
        self.seed_curated_jobs()

        self.stdout.write(self.style.SUCCESS(
            f"Catalog ready: movies={Movie.objects.count()} songs={Song.objects.count()} jobs={Job.objects.count()}"
        ))

    def seed_curated_movies(self):
        curated = [
            ("Harry Potter and the Sorcerer's Stone", "A young wizard begins his journey at Hogwarts.", "Fantasy, Adventure", "Daniel Radcliffe, Emma Watson, Rupert Grint", "Chris Columbus", 2001, 7.6, 96.0),
            ("Harry Potter and the Chamber of Secrets", "Harry returns for his second year as dark secrets unfold.", "Fantasy, Mystery", "Daniel Radcliffe, Emma Watson, Rupert Grint", "Chris Columbus", 2002, 7.4, 94.0),
            ("Harry Potter and the Prisoner of Azkaban", "A dangerous prisoner escapes and threatens Harry.", "Fantasy, Adventure", "Daniel Radcliffe, Emma Watson, Rupert Grint", "Alfonso Cuaron", 2004, 7.9, 95.0),
            ("Harry Potter and the Goblet of Fire", "Harry is forced into a deadly magical tournament.", "Fantasy, Adventure", "Daniel Radcliffe, Emma Watson, Rupert Grint", "Mike Newell", 2005, 7.7, 93.0),
            ("Harry Potter and the Order of the Phoenix", "Harry forms a student group against rising darkness.", "Fantasy, Action", "Daniel Radcliffe, Emma Watson, Rupert Grint", "David Yates", 2007, 7.5, 92.0),
            ("Harry Potter and the Half-Blood Prince", "Dark forces close in while secrets are revealed.", "Fantasy, Drama", "Daniel Radcliffe, Emma Watson, Rupert Grint", "David Yates", 2009, 7.6, 91.0),
            ("Harry Potter and the Deathly Hallows Part 1", "The trio leaves Hogwarts to destroy Horcruxes.", "Fantasy, Adventure", "Daniel Radcliffe, Emma Watson, Rupert Grint", "David Yates", 2010, 7.7, 90.0),
            ("Harry Potter and the Deathly Hallows Part 2", "The final battle at Hogwarts decides the wizarding world.", "Fantasy, Action", "Daniel Radcliffe, Emma Watson, Rupert Grint", "David Yates", 2011, 8.1, 98.0),
            ("Inception", "A thief enters dreams to plant an idea inside a guarded mind.", "Sci-Fi, Thriller", "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page", "Christopher Nolan", 2010, 8.8, 99.0),
            ("The Dark Knight", "Batman faces a criminal mastermind who wants Gotham to collapse into chaos.", "Action, Crime, Drama", "Christian Bale, Heath Ledger, Aaron Eckhart", "Christopher Nolan", 2008, 9.0, 99.0),
            ("Dangal", "A former wrestler trains his daughters to become world-class champions.", "Bollywood, Sports, Drama", "Aamir Khan, Fatima Sana Shaikh, Sanya Malhotra", "Nitesh Tiwari", 2016, 8.3, 97.0),
            ("3 Idiots", "Three engineering students challenge pressure, conformity, and career expectations.", "Bollywood, Comedy, Drama", "Aamir Khan, R. Madhavan, Sharman Joshi", "Rajkumar Hirani", 2009, 8.4, 98.0),
            ("Lagaan", "Villagers challenge British officers to a cricket match to escape taxes.", "Bollywood, Sports, Drama", "Aamir Khan, Gracy Singh, Rachel Shelley", "Ashutosh Gowariker", 2001, 8.1, 93.0),
            ("Gully Boy", "A Mumbai rapper rises through underground hip-hop and personal struggle.", "Bollywood, Music, Drama", "Ranveer Singh, Alia Bhatt, Siddhant Chaturvedi", "Zoya Akhtar", 2019, 7.9, 91.0),
            ("Zindagi Na Milegi Dobara", "Three friends rediscover courage, friendship, and love on a road trip.", "Bollywood, Comedy, Drama", "Hrithik Roshan, Farhan Akhtar, Abhay Deol", "Zoya Akhtar", 2011, 8.2, 94.0),
        ]
        for idx, row in enumerate(curated, start=1):
            title, overview, genres, cast, director, year, rating, popularity = row
            Movie.objects.update_or_create(
                tmdb_id=900000 + idx,
                defaults={
                    "title": title,
                    "overview": overview,
                    "genres": genres,
                    "cast": cast,
                    "director": director,
                    "release_year": year,
                    "runtime": 130 + idx,
                    "rating": rating,
                    "popularity": popularity,
                    "poster_url": "",
                },
            )

    def seed_curated_music(self):
        curated = [
            ("Dil Diyan Gallan", "Atif Aslam", "Tiger Zinda Hai", "Bollywood, Romantic", "romantic", 260000, 89, 92, 0.48, 0.52, 0.70),
            ("Dilbar", "Neha Kakkar", "Satyameva Jayate", "Bollywood, Dance", "party", 230000, 88, 120, 0.80, 0.82, 0.66),
            ("Dil Ibadat", "KK", "Tum Mile", "Bollywood, Romantic", "romantic", 305000, 84, 86, 0.42, 0.45, 0.78),
            ("Dil Se Re", "A.R. Rahman", "Dil Se", "Bollywood, Emotional", "dramatic", 365000, 82, 94, 0.57, 0.40, 0.50),
            ("Kal Ho Naa Ho", "Sonu Nigam", "Kal Ho Naa Ho", "Bollywood, Sad", "sad", 300000, 87, 76, 0.29, 0.33, 0.24),
            ("Chaiyya Chaiyya", "Sukhwinder Singh", "Dil Se", "Bollywood, Folk", "energetic", 410000, 86, 132, 0.76, 0.71, 0.73),
            ("Kesariya", "Arijit Singh", "Brahmastra", "Bollywood, Romantic", "romantic", 268000, 91, 94, 0.46, 0.58, 0.74),
            ("Apna Bana Le", "Arijit Singh", "Bhediya", "Bollywood, Romantic", "romantic", 262000, 88, 90, 0.40, 0.50, 0.68),
            ("Naatu Naatu", "Rahul Sipligunj", "RRR", "Dance, Telugu, Indian", "party", 215000, 92, 150, 0.92, 0.88, 0.80),
            ("Kar Har Maidaan Fateh", "Sukhwinder Singh", "Sanju", "Bollywood, Motivational", "uplifting", 334000, 82, 118, 0.78, 0.55, 0.72),
            ("Kun Faya Kun", "A.R. Rahman", "Rockstar", "Bollywood, Sufi", "calm", 470000, 86, 82, 0.26, 0.28, 0.52),
        ]
        for idx, row in enumerate(curated, start=1):
            title, artist_name, album, genres, mood, duration, popularity, tempo, energy, danceability, valence = row
            artist, _ = Artist.objects.update_or_create(
                spotify_id=f"curated_artist_{idx:03d}",
                defaults={"name": artist_name, "genres": genres, "popularity": popularity, "followers": 100000 + idx * 1000},
            )
            Song.objects.update_or_create(
                spotify_id=f"curated_song_{idx:03d}",
                defaults={
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "genres": genres,
                    "mood": mood,
                    "duration_ms": duration,
                    "popularity": popularity,
                    "tempo": float(tempo),
                    "energy": float(energy),
                    "danceability": float(danceability),
                    "valence": float(valence),
                    "acousticness": 0.30,
                    "preview_url": "",
                    "image_url": "",
                },
            )

    def seed_curated_jobs(self):
        curated = [
            ("india_ai_resume_001", "AI Full Stack Engineer", "TuringMinds India", "Bengaluru", "Python, Django, React, NLP, RAG, PostgreSQL, Docker", 1800000, 3200000, "full-time"),
            ("india_ml_002", "Machine Learning Engineer - NLP", "BharatAI Labs", "Hyderabad", "Python, NLP, scikit-learn, pandas, FastAPI, MLOps", 1400000, 2600000, "hybrid"),
            ("india_data_003", "Data Scientist", "FinSight Analytics", "Mumbai", "Python, SQL, machine learning, statistics, Power BI, Tableau", 1200000, 2400000, "full-time"),
            ("india_react_004", "React Frontend Engineer", "PixelWorks Tech", "Pune", "React, TypeScript, REST, UX, testing, performance", 900000, 1800000, "hybrid"),
            ("india_django_005", "Django Backend Developer", "CloudCart India", "Noida", "Python, Django, PostgreSQL, Redis, Docker, AWS", 1000000, 2100000, "full-time"),
            ("india_devops_006", "Cloud DevOps Engineer", "InfraNest", "Gurgaon", "AWS, Kubernetes, Terraform, CI/CD, Docker, monitoring", 1500000, 3000000, "remote"),
            ("india_bi_007", "Business Intelligence Analyst", "MarketPulse", "Delhi", "SQL, Power BI, Tableau, Python, dashboards, analytics", 800000, 1600000, "full-time"),
            ("india_genai_008", "Generative AI Engineer", "PromptStack", "Remote India", "LLM, RAG, LangChain, Python, vector databases, APIs", 1800000, 3600000, "remote"),
        ]
        for job_id, title, company_name, location, skills, salary_min, salary_max, job_type in curated:
            company, _ = Company.objects.update_or_create(
                name=company_name,
                defaults={
                    "location": location,
                    "description": "India-based technology company hiring for production AI and software roles.",
                },
            )
            Job.objects.update_or_create(
                job_id=job_id,
                defaults={
                    "title": title,
                    "company": company,
                    "location": location,
                    "description": f"Build production-grade features and intelligent systems using {skills}.",
                    "requirements": f"Hands-on portfolio or professional experience with {skills}. Strong communication and product thinking.",
                    "skills": skills,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "job_type": job_type,
                    "apply_url": "",
                    "posted_at": date.today(),
                },
            )
