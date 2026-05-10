$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  python -m venv .venv
}

$python = ".\.venv\Scripts\python.exe"

& $python -c "import django" 2>$null
if ($LASTEXITCODE -ne 0) {
  & $python -m pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

& $python manage.py migrate --noinput

$movieCount = & $python manage.py shell -c "from apps.movies.models import Movie; print(Movie.objects.count())"
if ([int]$movieCount -lt 10000) {
  & $python manage.py generate_catalog --count 10000
}

$existing = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
  Stop-Process -Id $existing.OwningProcess -Force
  Start-Sleep -Seconds 1
}

Write-Host "RecommAI is running at http://127.0.0.1:8000/"
& $python manage.py runserver 127.0.0.1:8000
