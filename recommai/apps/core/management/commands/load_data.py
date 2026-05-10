from datetime import date

from django.core.management.base import BaseCommand

from apps.jobs.models import Company, Job
from apps.movies.models import Movie
from apps.music.models import Artist, Song


class Command(BaseCommand):
    help = "Load sample movies, songs, and jobs for a quick demo."

    def handle(self, *args, **options):
        movies = [
            ("Inception", "Dream heist thriller with layered realities.", "Sci-Fi, Action", "Leonardo DiCaprio, Joseph Gordon-Levitt", "Christopher Nolan", 2010, 8.8),
            ("Interstellar", "Explorers travel through a wormhole to save humanity.", "Sci-Fi, Drama", "Matthew McConaughey, Anne Hathaway", "Christopher Nolan", 2014, 8.7),
            ("The Social Network", "The founding story of Facebook and its conflicts.", "Drama, Biography", "Jesse Eisenberg, Andrew Garfield", "David Fincher", 2010, 7.8),
            ("Arrival", "A linguist decodes alien communication.", "Sci-Fi, Drama", "Amy Adams, Jeremy Renner", "Denis Villeneuve", 2016, 7.9),
            ("Whiplash", "A jazz drummer faces an intense instructor.", "Drama, Music", "Miles Teller, J.K. Simmons", "Damien Chazelle", 2014, 8.5),
            ("3 Idiots", "Engineering students challenge pressure and chase real learning.", "Bollywood, Comedy, Drama", "Aamir Khan, R. Madhavan", "Rajkumar Hirani", 2009, 8.4),
            ("Dangal", "A wrestler trains his daughters for international glory.", "Bollywood, Sports, Drama", "Aamir Khan, Fatima Sana Shaikh", "Nitesh Tiwari", 2016, 8.3),
            ("Gully Boy", "A Mumbai rapper rises through music and ambition.", "Bollywood, Music, Drama", "Ranveer Singh, Alia Bhatt", "Zoya Akhtar", 2019, 7.9),
        ]
        for title, overview, genres, cast, director, year, rating in movies:
            Movie.objects.update_or_create(title=title, defaults={
                "overview": overview, "genres": genres, "cast": cast, "director": director,
                "release_year": year, "rating": rating, "popularity": rating * 10,
            })

        songs = [
            ("Blinding Lights", "The Weeknd", "After Hours", "Synthpop", "energetic", 171000, 95, 171, 0.73, 0.51, 0.33),
            ("Bohemian Rhapsody", "Queen", "A Night at the Opera", "Rock", "dramatic", 354000, 89, 144, 0.40, 0.39, 0.23),
            ("Levitating", "Dua Lipa", "Future Nostalgia", "Pop", "bright", 203000, 88, 103, 0.82, 0.70, 0.92),
            ("Lose Yourself", "Eminem", "8 Mile", "Hip-Hop", "motivational", 326000, 91, 171, 0.74, 0.69, 0.06),
            ("Clair de Lune", "Claude Debussy", "Suite bergamasque", "Classical", "calm", 300000, 70, 66, 0.12, 0.19, 0.92),
            ("Kesariya", "Arijit Singh", "Brahmastra", "Bollywood", "romantic", 268000, 91, 94, 0.46, 0.58, 0.28),
            ("Naatu Naatu", "Rahul Sipligunj", "RRR", "Indian Dance", "party", 215000, 92, 150, 0.92, 0.88, 0.20),
            ("Kun Faya Kun", "A.R. Rahman", "Rockstar", "Bollywood Sufi", "calm", 470000, 86, 82, 0.26, 0.28, 0.62),
        ]
        for title, artist_name, album, genres, mood, duration, popularity, tempo, energy, danceability, acousticness in songs:
            artist, _ = Artist.objects.get_or_create(name=artist_name, defaults={"genres": genres, "popularity": popularity})
            Song.objects.update_or_create(title=title, artist=artist, defaults={
                "album": album, "genres": genres, "mood": mood, "duration_ms": duration,
                "popularity": popularity, "tempo": tempo, "energy": energy,
                "danceability": danceability, "acousticness": acousticness,
            })

        jobs = [
            ("Senior Django Engineer", "Northstar Labs", "Remote", "Python, Django, PostgreSQL, REST", 120000, 170000),
            ("Machine Learning Engineer", "SignalWorks AI", "Bengaluru", "Python, NLP, scikit-learn, MLOps", 90000, 150000),
            ("Frontend Product Engineer", "CanvasOps", "Delhi", "React, TypeScript, UX, APIs", 70000, 120000),
            ("Data Analyst", "InsightGrid", "Mumbai", "SQL, Python, Dashboards, Statistics", 50000, 90000),
            ("Cloud DevOps Engineer", "DeployHQ", "Remote", "Docker, AWS, CI/CD, Terraform", 100000, 160000),
            ("Generative AI Engineer", "PromptStack", "Remote India", "LLM, RAG, LangChain, Python, vector databases", 180000, 360000),
            ("Django Backend Developer", "CloudCart India", "Noida", "Python, Django, PostgreSQL, Redis, Docker, AWS", 100000, 210000),
            ("React Frontend Engineer", "PixelWorks Tech", "Pune", "React, TypeScript, REST, UX, testing", 90000, 180000),
        ]
        for title, company_name, location, skills, salary_min, salary_max in jobs:
            company, _ = Company.objects.get_or_create(name=company_name, defaults={"location": location})
            Job.objects.update_or_create(title=title, company=company, defaults={
                "location": location,
                "description": f"Build production systems using {skills}.",
                "requirements": f"Strong experience with {skills}.",
                "skills": skills,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "job_type": "full-time",
                "posted_at": date.today(),
            })

        self.stdout.write(self.style.SUCCESS("Loaded RecommAI sample data."))
