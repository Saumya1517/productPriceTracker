#!/usr/bin/env bash
# Build script for Vercel deployment
echo "=== [VERCEL BUILD] Installing dependencies ==="
python3 -m pip install -r requirements.txt --break-system-packages

echo "=== [VERCEL BUILD] Collecting static files ==="
mkdir -p staticfiles
python3 manage.py collectstatic --no-input

echo "=== [VERCEL BUILD] Static build complete ==="
