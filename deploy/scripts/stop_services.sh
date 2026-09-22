#!/usr/bin/env bash
echo "Stopping GTU-ITR Portal & Tunnel..."
pkill -f "gunicorn.*wsgi:app" 2>/dev/null || true
pkill -f "cloudflared.*tunnel run" 2>/dev/null || true
echo "Stopped."
