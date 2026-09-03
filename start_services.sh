#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal & Tunnel - Background Starter with Logging
# ==============================================================================
PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
cd "$PROJECT_DIR"

mkdir -p "$PROJECT_DIR/logs"

echo "Stopping any existing portal, server UI, and tunnel instances..."
pkill -f "gunicorn.*wsgi:app" 2>/dev/null || true
pkill -f "gunicorn.*gtu-server-ui" 2>/dev/null || true
pkill -f "cloudflared.*tunnel run" 2>/dev/null || true
sleep 1

# Ensure PostgreSQL 16 is running
export LD_LIBRARY_PATH="/home/gtu-itr/pgsql/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}:/snap/antigravity-cli/19/usr/lib/x86_64-linux-gnu"
PG_BIN="/home/gtu-itr/pgsql/usr/lib/postgresql/16/bin"
PG_DATA="/home/gtu-itr/pgsql/data"
if [ -d "$PG_DATA" ]; then
    if ! "$PG_BIN/pg_isready" -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
        echo "Starting PostgreSQL 16 database server..."
        "$PG_BIN/pg_ctl" -D "$PG_DATA" -l /home/gtu-itr/pgsql/postgres.log start || true
        sleep 2
    else
        echo "PostgreSQL 16 is already active."
    fi
fi

echo "Starting GTU-ITR Portal (Gunicorn on 5000)..."
"$PROJECT_DIR/venv/bin/gunicorn" \
    --bind 0.0.0.0:5000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile "$PROJECT_DIR/logs/portal_access.log" \
    --error-logfile "$PROJECT_DIR/logs/portal_error.log" \
    --capture-output \
    --daemon \
    wsgi:app

echo "Starting GTU-ITR Server UI & Terminal (Gunicorn on 7000)..."
/home/gtu-itr/gtu-server-ui/start_server_ui.sh

echo "Starting Cloudflare Tunnel (daemonized)..."
"$PROJECT_DIR/venv/bin/python3" -c "
import os, sys, subprocess
if os.fork() > 0:
    sys.exit(0)
os.setsid()
if os.fork() > 0:
    sys.exit(0)
sys.stdout.flush()
sys.stderr.flush()
with open(os.devnull, 'r') as devnull:
    os.dup2(devnull.fileno(), sys.stdin.fileno())
cmd = [
    '$PROJECT_DIR/venv/bin/cloudflared',
    '--config', '$PROJECT_DIR/.cloudflared/config.yml',
    '--logfile', '$PROJECT_DIR/logs/tunnel.log',
    '--loglevel', 'info',
    'tunnel', 'run', '0db9da8f-002e-4e4c-8f89-c5d548652de7'
]
subprocess.Popen(cmd, close_fds=True)
"

sleep 3
echo ""
echo "======================================================================"
echo " [SUCCESS] All Services are up and running!"
echo " 1. Portal Web App:  https://iic-gtu-itr.aceglory.in  (Port 5000)"
echo " 2. Server Console:  https://gtu-itr-server.aceglory.in (Port 7000)"
echo "                     [Local: http://localhost:7000]"
echo " 3. Database:        PostgreSQL 16 (iic_cell_gtu on 127.0.0.1:5432)"
echo ""
echo " Server UI Login:"
echo "   ID / Username: admin"
echo "   Password:      gtu-itr@2026"
echo ""
echo " Log files:"
echo "   - Access requests: tail -f $PROJECT_DIR/logs/portal_access.log"
echo "   - Portal errors:   tail -f $PROJECT_DIR/logs/portal_error.log"
echo "   - Server UI logs:  tail -f /home/gtu-itr/gtu-server-ui/logs/access.log"
echo "   - Tunnel activity: tail -f $PROJECT_DIR/logs/tunnel.log"
echo "======================================================================"
