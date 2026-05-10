#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env || true
python manage.py makemigrations
python manage.py migrate
python manage.py load_data
python manage.py collectstatic --noinput
echo "RecommAI is ready. Run: python manage.py runserver"
