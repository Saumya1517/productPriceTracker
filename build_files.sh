#!/usr/bin/env bash
# Build script for Vercel deployment
echo "=== [VERCEL BUILD] Installing dependencies ==="
python3 -m pip install -r requirements.txt

echo "=== [VERCEL BUILD] Collecting static files ==="
python3 manage.py collectstatic --no-input --clear

echo "=== [VERCEL BUILD] Static build complete ==="
