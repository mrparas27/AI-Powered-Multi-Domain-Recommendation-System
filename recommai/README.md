# AI Powered Multi Domain Recommendation System

A production-ready Django web application that recommends movies, music, and jobs from one authenticated dashboard. The system combines local fallback datasets, external API integrations, content-based similarity, resume parsing, skill extraction, and role-aware job matching.

## Live Demo

- App: [https://ai-powered-multi-domain-recommendation-wofc.onrender.com/](https://ai-powered-multi-domain-recommendation-wofc.onrender.com/)
- Music Recommendation: [https://ai-powered-multi-domain-recommendation-wofc.onrender.com/music/](https://ai-powered-multi-domain-recommendation-wofc.onrender.com/music/)

## Features

- Secure signup, login, logout, and user dashboard.
- Movie recommendation by title, genre, overview, cast, director, and cosine similarity.
- Similar movie search for titles such as `3 Idiots`, `Dangal`, `Inception`, and other Hollywood/Bollywood movies.
- Movie posters from TMDB when reachable, with fallback poster/artwork support for important catalog titles.
- Music recommendation by mood such as romantic, calm, party, energetic, sad, focus, and uplifting.
- Live music search with Spotify support and fallback artwork provider.
- Job recommendation from resume text, TXT, PDF, or DOCX upload.
- Resume skill extraction and suggested roles such as AI Full Stack Engineer, Generative AI Engineer, Machine Learning Engineer, Django Backend Developer, React Frontend Engineer, Data Analyst, and Cloud DevOps Engineer.
- Live job search with external provider support plus India-focused local fallback jobs.
- REST APIs for local recommendation and live provider search.
- SQLite for local development and PostgreSQL-ready production deployment.
- WhiteNoise static file support and Gunicorn-ready Dockerfile.

## Tech Stack

- Backend: Django 4.2, Django REST Framework
- Auth: Django session auth and Simple JWT endpoints
- Database: SQLite locally, PostgreSQL in production
- Recommendation Engine: tokenization plus cosine similarity
- Resume Parsing: `pypdf` and `python-docx`
- External APIs: TMDB, Spotify, JSearch/RapidAPI, SerpAPI, WeatherAPI, GitHub, fallback artwork/search providers
- Static Files: WhiteNoise
- Production Server: Gunicorn

## Project Structure

```text
recommai/
  apps/
    core/              # Pages, local APIs, resume parsing, recommendation views
    movies/            # Movie model, admin, curated poster helpers
    music/             # Artist and song models
    jobs/              # Company and job models
    recommendations/   # Cosine similarity engine and recommendation logs
    external_apis/     # TMDB, Spotify, job, search, weather, and fallback API clients
    users/             # User profile model and signals
  config/              # Django settings, URLs, WSGI/ASGI
  templates/           # Auth, dashboard, movies, music, jobs UI
  static/              # CSS and JavaScript
  manage.py
  run_app.ps1
  requirements.txt
  requirements-postgres.txt
  Dockerfile
```

## Local Setup

From PowerShell:

```powershell
cd "C:\Users\Mr Paras Sharma\OneDrive\Desktop\AI-Based Multi-Domain Recommendation System\recommai"
powershell -ExecutionPolicy Bypass -File .\run_app.ps1
```

The script will:

- Create `.venv` if missing.
- Install Python dependencies.
- Create `.env` from `.env.example` if missing.
- Run migrations.
- Generate/load demo catalog data when needed.
- Start Django at `http://127.0.0.1:8000/`.

Open the app:

- Web app: `http://127.0.0.1:8000/`
- Dashboard: `http://127.0.0.1:8000/dashboard/`
- Admin: `http://127.0.0.1:8000/admin/`
- API health: `http://127.0.0.1:8000/api/v1/health/`

## Manual Setup

```powershell
cd "C:\Users\Mr Paras Sharma\OneDrive\Desktop\AI-Based Multi-Domain Recommendation System\recommai"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py load_data
python manage.py generate_catalog --count 10000
python manage.py runserver 127.0.0.1:8000
```

If `python` is not recognized on Windows, use the full Python executable path or run the included `run_app.ps1` script.

## Environment Variables

Create a `.env` file in the `recommai` folder.

```env
DJANGO_SECRET_KEY=change-this-to-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=
TIME_ZONE=Asia/Kolkata

TMDB_API_KEY=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
JOBHUNTER_API_KEY=
GITHUB_TOKEN=
SERPAPI_API_KEY=
WEATHER_API_KEY=
EXTERNAL_CACHE_TTL_SECONDS=3600
```

Do not commit real API keys to GitHub. Keep production secrets in the hosting provider environment variable dashboard.

## Main Pages

- `/accounts/signup/` creates a new user account.
- `/accounts/login/` logs in existing users.
- `/dashboard/` shows catalog counts, profile data, and recent recommendation activity.
- `/movies/` searches movies and finds similar movies using cosine similarity.
- `/music/` searches music and recommends songs by mood.
- `/jobs/` parses resumes, extracts skills, suggests roles, and recommends matching jobs.

## API Endpoints

Local recommendation APIs:

```http
GET /api/v1/health/
GET /api/v1/movies/?q=3%20Idiots
GET /api/v1/music/?q=romantic
GET /api/v1/jobs/?q=python
GET /api/v1/recommendations/?domain=movies&q=engineering%20college%20comedy
GET /api/v1/recommendations/?domain=music&q=romantic%20bollywood
GET /api/v1/recommendations/?domain=jobs&q=python%20django%20react%20nlp
GET /api/v1/movies/similar/1/
GET /api/v1/music/mood/?mood=party
GET /api/v1/jobs/resume-match/?resume=Python%20Django%20React%20NLP
```

Live provider APIs:

```http
GET /api/v1/live/status/
GET /api/v1/live/movies/search/?q=3%20Idiots
GET /api/v1/live/movies/trending/
GET /api/v1/live/music/search/?q=Arijit%20Singh
GET /api/v1/live/music/trending/?country=IN
GET /api/v1/live/jobs/search/?q=python%20django&location=Bengaluru
GET /api/v1/live/github/repositories/?q=django%20recommendation
GET /api/v1/live/weather/current/?location=Delhi
```

## Recommendation Logic

Movies are recommended by comparing a selected movie against other movies using text from:

- title
- overview
- genres
- cast
- director

Jobs are recommended by extracting skills from resume content and comparing those skills against:

- job title
- company
- location
- description
- requirements
- skills

Music mood recommendation compares mood targets against:

- energy
- danceability
- valence
- popularity
- genre and mood tags

## Data Loading

Load a small demo dataset:

```powershell
python manage.py load_data
```

Generate a larger local fallback catalog:

```powershell
python manage.py generate_catalog --count 10000
```

This is useful because the app remains functional even if an external API is unavailable.

## Production Deployment

Recommended one-place deployment: **Render**.

Render is a strong fit because this app is a Django server application that needs:

- one web service
- one PostgreSQL database
- environment variables for API keys
- Gunicorn
- WhiteNoise static files
- optional Docker deployment

### Render Deployment Steps

1. Push the project to GitHub.
2. Create a new PostgreSQL database on Render.
3. Create a new Web Service on Render from the GitHub repository.
4. If Render is using Docker, leave the root directory blank. The repository root now has a Dockerfile that copies the `recommai` app correctly.
5. If Render is using the Python environment instead of Docker, set the root directory to `recommai`.
6. Add production environment variables in Render.
7. Redeploy. The startup script runs migrations automatically.

Recommended Render settings for Python environment:

```text
Root Directory: recommai
Build Command: pip install -r requirements.txt
Start Command: bash start.sh
```

Recommended Render settings for Docker environment:

```text
Root Directory: leave blank
Dockerfile Path: Dockerfile
```

Production environment variables:

```env
DJANGO_SECRET_KEY=your-secure-production-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-render-domain.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-render-domain.onrender.com
DATABASE_URL=postgresql://user:password@host:5432/database
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

TMDB_API_KEY=your-tmdb-key
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
JOBHUNTER_API_KEY=your-job-api-key
SERPAPI_API_KEY=your-serpapi-key
WEATHER_API_KEY=your-weather-api-key
GITHUB_TOKEN=your-github-token
```

Important: `DATABASE_URL` must be set to the Render PostgreSQL **Internal Database URL** and it must start with `postgres://` or `postgresql://`. If it is missing or malformed, the app falls back to SQLite; that can run, but signup/login data will not be durable on Render.

For your current Render URL, use:

```env
DJANGO_ALLOWED_HOSTS=ai-powered-multi-domain-recommendation-wofc.onrender.com
CSRF_TRUSTED_ORIGINS=https://ai-powered-multi-domain-recommendation-wofc.onrender.com
TIME_ZONE=Asia/Kolkata
```

Render also provides `RENDER_EXTERNAL_HOSTNAME`; the app automatically accepts that hostname when it is present.

Do not put `Asia/Kolkata` in `CSRF_TRUSTED_ORIGINS`. `CSRF_TRUSTED_ORIGINS` only accepts full origins starting with `http://` or `https://`. The app ignores malformed CSRF values defensively, but the correct Render setup is still:

```env
CSRF_TRUSTED_ORIGINS=https://ai-powered-multi-domain-recommendation-wofc.onrender.com
TIME_ZONE=Asia/Kolkata
```

### Fix Render DisallowedHost Error

If Render shows this error:

```text
Invalid HTTP_HOST header: 'your-app.onrender.com'. You may need to add 'your-app.onrender.com' to ALLOWED_HOSTS.
```

Add these environment variables in Render, then redeploy:

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ai-powered-multi-domain-recommendation-wofc.onrender.com
CSRF_TRUSTED_ORIGINS=https://ai-powered-multi-domain-recommendation-wofc.onrender.com
TIME_ZONE=Asia/Kolkata
```

If Render currently has `CSRF_TRUSTED_ORIGINS=Asia/Kolkata`, replace it with the HTTPS URL above.

The app also supports Render auto-detection through `RENDER_EXTERNAL_HOSTNAME`, so future Render domains are accepted automatically when Render provides that variable.

After changing environment variables in Render:

1. Open the Render web service dashboard.
2. Go to Environment.
3. Add or update the variables above.
4. Click Manual Deploy.
5. Choose Deploy latest commit.

For PostgreSQL, install the production database dependency:

```powershell
pip install -r requirements-postgres.txt
```

If deploying with Docker, update the Docker build to install `requirements-postgres.txt` or add `psycopg2-binary` to the main production requirements.

## Alternative Deployment Options

- Render: best one-place option for this app.
- Railway: also good for Django plus PostgreSQL and fast demos.
- Fly.io: powerful but more DevOps-heavy.
- Vercel: not recommended as the main host for this project because this is a full Django server app, not a frontend-only app.

## Common Issues

### Signup fails with no such table: auth_user

This means migrations did not run on the deployed database, or Render is using SQLite without an initialized `db.sqlite3`.

Fix on Render:

1. Create or attach a Render PostgreSQL database.
2. Set `DATABASE_URL` to the PostgreSQL internal database URL. It must start with `postgres://` or `postgresql://`; do not paste only the host, database name, or a placeholder.
3. If using Python environment, set the Start Command to `bash start.sh`. If using Docker, redeploy with the root `Dockerfile`.
4. Redeploy latest commit.

The `start.sh` script runs `python manage.py migrate --noinput` before starting Gunicorn, so Django auth tables such as `auth_user` are created automatically.

### TMDB key is correct but app shows fallback results

This usually means the machine or hosting environment cannot reach `api.themoviedb.org` quickly enough. The app will still recommend movies using local data and poster fallbacks. On deployment, TMDB usually works normally if outbound networking is allowed.

### PDF resume does not parse

If the PDF is scanned/image-only, it may not contain readable text. Use a text-based PDF, DOCX, TXT, or paste the resume text directly into the app.

### No job results from live API

Check the job provider key and quota. The app still uses India-focused fallback jobs and resume skill matching when live APIs fail.

## Useful Commands

```powershell
python manage.py check
python manage.py migrate
python manage.py load_data
python manage.py generate_catalog --count 10000
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver 127.0.0.1:8000
```

## License

This project is intended for learning, portfolio, and production-style demonstration use.
