#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR 24/7 Watchdog - Auto-reconnect & Process Guardian
# ==============================================================================
PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
SERVER_UI_DIR="/home/gtu-itr/gtu-server-ui"
LOG_FILE="$PROJECT_DIR/logs/watchdog.log"
mkdir -p "$PROJECT_DIR/logs"

unset PYTHONPATH
unset PYTHONHOME
export PATH="/home/gtu-itr/iic-cell-gtu-itr-/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin"

# Ensure single instance
exec 200>/tmp/gtu_watchdog.lock
flock -n 200 || { echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another Watchdog instance is already running. Exiting." >> "$LOG_FILE"; exit 0; }

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Watchdog guardian started (PID: $$)." >> "$LOG_FILE"

while true; do
    # 1. Check PostgreSQL Database
    if ! pgrep -f "/home/gtu-itr/pgsql/usr/lib/postgresql/16/bin/postgres" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [RECOVERY] PostgreSQL down, restarting..." >> "$LOG_FILE"
        export LD_LIBRARY_PATH="/home/gtu-itr/pgsql/usr/lib/x86_64-linux-gnu"
        /home/gtu-itr/pgsql/usr/lib/postgresql/16/bin/pg_ctl -D /home/gtu-itr/pgsql/data -l /home/gtu-itr/pgsql/postgres.log start >> "$LOG_FILE" 2>&1
        sleep 2
    fi

    # 2. Check GTU-ITR Portal (Port 5000)
    if ! pgrep -f "gunicorn.*wsgi:app" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [RECOVERY] Portal Web App down, restarting..." >> "$LOG_FILE"
        export DATABASE_URL="postgresql+psycopg2://gtu_admin:44113290@localhost:5432/iic_cell_gtu"
        export LD_LIBRARY_PATH="/home/gtu-itr/pgsql/usr/lib/x86_64-linux-gnu"
        unset PYTHONPATH
        unset PYTHONHOME
        GUNICORN_BIN="/usr/bin/gunicorn"
        if [ ! -x "$GUNICORN_BIN" ]; then
            GUNICORN_BIN="$PROJECT_DIR/venv/bin/gunicorn"
        fi
        $GUNICORN_BIN \
            --bind 0.0.0.0:5000 \
            --workers 3 \
            --timeout 120 \
            --access-logfile "$PROJECT_DIR/logs/portal_access.log" \
            --error-logfile "$PROJECT_DIR/logs/portal_error.log" \
            --capture-output \
            --daemon \
            wsgi:app >> "$LOG_FILE" 2>&1
        sleep 2
    fi

    # 3. Check GTU-ITR Server UI & Terminal (Port 7000)
    if ! pgrep -f "gunicorn.*gtu-server-ui" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [RECOVERY] Server UI down, restarting..." >> "$LOG_FILE"
        "$SERVER_UI_DIR/start_server_ui.sh" >> "$LOG_FILE" 2>&1
        sleep 2
    fi

    # 4. Check Cloudflare Tunnel
    if ! pgrep -f "cloudflared.*tunnel run" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [RECOVERY] Cloudflare Tunnel down, restarting..." >> "$LOG_FILE"
        "$PROJECT_DIR/venv/bin/python3" -c "
import os, sys, subprocess
if os.fork() > 0: sys.exit(0)
os.setsid()
if os.fork() > 0: sys.exit(0)
cmd = [
    '$PROJECT_DIR/venv/bin/cloudflared',
    '--config', '$PROJECT_DIR/.cloudflared/config.yml',
    '--logfile', '$PROJECT_DIR/logs/tunnel.log',
    '--loglevel', 'info',
    'tunnel', 'run', '0db9da8f-002e-4e4c-8f89-c5d548652de7'
]
subprocess.Popen(cmd, close_fds=True)
"
    fi

    # 5. Check Ollama AI Server (Port 11434)
    if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [RECOVERY] Ollama AI Server down, restarting..." >> "$LOG_FILE"
        /bin/bash /home/gtu-itr/ollama/start_ollama.sh >> "$LOG_FILE" 2>&1
        sleep 2
    fi

    # 6. Check Portal Restart Trigger File
    if [ -f "$PROJECT_DIR/.restart_portal" ]; then
        rm -f "$PROJECT_DIR/.restart_portal"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Portal restart requested via trigger file..." >> "$LOG_FILE"
        pkill -f "gunicorn.*wsgi:app" 2>/dev/null || true
        sleep 2
    fi

    # 7. Background Auto-Sync SIH Results Photos (Every 60 seconds)
    SYNC_COUNTER=$(( (SYNC_COUNTER + 1) % 6 ))
    if [ "$SYNC_COUNTER" -eq 0 ] || [ -f "$PROJECT_DIR/.sync_results" ]; then
        rm -f "$PROJECT_DIR/.sync_results"
        "$PROJECT_DIR/venv/bin/python3" -c "from utils.results_sync import get_live_results_data; get_live_results_data()" >> "$LOG_FILE" 2>&1 || true
    fi

    sleep 10
done
