#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal - Quick Runner Script
# ==============================================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    echo "[ERROR] Virtualenv not found at $PROJECT_DIR/venv"
    exit 1
fi

echo "======================================================================"
echo " Starting GTU-ITR Portal (Gunicorn on 0.0.0.0:5000)..."
echo "======================================================================"

exec ./venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 --timeout 120 wsgi:app
