#!/usr/bin/env bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

python manage.py shell -c "from apps.movies.models import Movie; from django.core.management import call_command; call_command('load_data') if Movie.objects.count() == 0 else None"

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
