# Real-Time API Guide

Add these keys to `.env`:

- TMDB: `TMDB_API_KEY`
- Spotify: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`
- JobHunter: `JOBHUNTER_API_KEY`
- GitHub: `GITHUB_TOKEN`

The external API layer normalizes third-party responses into stable JSON fields for the frontend and import tools. Results are cached in the database using a configurable TTL:

```env
EXTERNAL_CACHE_TTL_SECONDS=3600
```

Example:

```bash
curl "http://localhost:8000/api/v1/external/movies/search/?q=inception"
curl "http://localhost:8000/api/v1/external/music/search/?q=bohemian+rhapsody"
curl "http://localhost:8000/api/v1/external/jobs/search/?q=python+developer&location=remote"
curl "http://localhost:8000/api/v1/external/web/search/?q=ai+recommendation+systems"
curl "http://localhost:8000/api/v1/external/weather/current/?location=Delhi"
```
