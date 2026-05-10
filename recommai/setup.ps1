$ErrorActionPreference = "Stop"

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}
python manage.py makemigrations
python manage.py migrate
python manage.py load_data
python manage.py collectstatic --noinput
Write-Host "RecommAI is ready. Run: python manage.py runserver"
