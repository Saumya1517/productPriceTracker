#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=== [RENDER BUILD] Installing Python Dependencies ==="
pip install -r requirements.txt

echo "=== [RENDER BUILD] Installing Playwright Chromium Browser ==="
playwright install chromium
playwright install-deps chromium || true

echo "=== [RENDER BUILD] Collecting Static Files ==="
python manage.py collectstatic --no-input

echo "=== [RENDER BUILD] Applying Database Migrations ==="
python manage.py migrate

echo "=== [RENDER BUILD] Build Complete Successfully! ==="
