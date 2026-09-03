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

mkdir -p "$PROJECT_DIR/logs"

exec ./venv/bin/gunicorn --bind 0.0.0.0:5000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile "$PROJECT_DIR/logs/portal_access.log" \
    --error-logfile "$PROJECT_DIR/logs/portal_error.log" \
    --capture-output \
    wsgi:app

