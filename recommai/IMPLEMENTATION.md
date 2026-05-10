# Implementation Notes

## Architecture

- `config/`: Django project settings and routing.
- `apps/core/`: pages, local APIs, serializers, and demo data loader.
- `apps/movies/`, `apps/music/`, `apps/jobs/`: domain models and admin.
- `apps/recommendations/`: recommendation event logging and content-similarity engine.
- `apps/external_apis/`: provider clients, response cache, request logs, and import endpoints.

## Recommendation Engine

The engine uses tokenized cosine similarity for reliable, dependency-light content recommendations. It can be replaced with scikit-learn TF-IDF later without changing the public API shape.

## Security

Secrets live in environment variables. Production should run with `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, HTTPS, and PostgreSQL through `DATABASE_URL`.
