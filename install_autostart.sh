#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Server & Portal - 1-Click Permanent Auto-Start on Machine Boot
# ==============================================================================
set +e

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Please run this script with sudo: sudo bash install_autostart.sh"
  exit 1
fi

PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
SERVER_UI_DIR="/home/gtu-itr/gtu-server-ui"

POSTGRES_SRC="$PROJECT_DIR/gtu-postgres.service"
PORTAL_SRC="$PROJECT_DIR/gtu-portal.service"
SERVER_UI_SRC="$SERVER_UI_DIR/gtu-server-ui.service"
TUNNEL_SRC="$PROJECT_DIR/gtu-tunnel.service"
WATCHDOG_SRC="$PROJECT_DIR/gtu-watchdog.service"

POSTGRES_DEST="/etc/systemd/system/gtu-postgres.service"
PORTAL_DEST="/etc/systemd/system/gtu-portal.service"
SERVER_UI_DEST="/etc/systemd/system/gtu-server-ui.service"
TUNNEL_DEST="/etc/systemd/system/gtu-tunnel.service"
WATCHDOG_DEST="/etc/systemd/system/gtu-watchdog.service"

echo "======================================================================"
echo " Setting up Permanent Auto-Start on Server Boot (Power Cut & Crash Resilient)"
echo " 1. PostgreSQL DB:     127.0.0.1:5432 (iic_cell_gtu)"
echo " 2. Portal Web App:    https://iic-gtu-itr.aceglory.in  (Port 5000)"
echo " 3. Server Console:    https://gtu-itr-server.aceglory.in (Port 7000)"
echo " 4. Cloudflare Tunnel: 0db9da8f-002e-4e4c-8f89-c5d548652de7"
echo " 5. Watchdog Guardian: 24/7 Self-Healing & Process Supervisor"
echo "======================================================================"

echo ""
echo "--> [1/6] Stopping any existing manual background instances..."
pkill -f "watchdog.sh" 2>/dev/null || true
pkill -f "gunicorn.*wsgi:app" 2>/dev/null || true
pkill -f "gunicorn.*gtu-server-ui" 2>/dev/null || true
pkill -f "cloudflared.*tunnel run" 2>/dev/null || true

echo "--> [2/6] Installing systemd service units to /etc/systemd/system/..."
cp "$POSTGRES_SRC" "$POSTGRES_DEST"
cp "$PORTAL_SRC" "$PORTAL_DEST"
cp "$SERVER_UI_SRC" "$SERVER_UI_DEST"
cp "$TUNNEL_SRC" "$TUNNEL_DEST"
cp "$WATCHDOG_SRC" "$WATCHDOG_DEST"
chmod 644 "$POSTGRES_DEST" "$PORTAL_DEST" "$SERVER_UI_DEST" "$TUNNEL_DEST" "$WATCHDOG_DEST"

echo "--> [3/6] Reloading systemd daemon..."
systemctl daemon-reload

echo "--> [4/6] Enabling persistent lingering and auto-start on machine boot..."
loginctl enable-linger gtu-itr 2>/dev/null || true
systemctl enable gtu-postgres.service
systemctl enable gtu-portal.service
systemctl enable gtu-server-ui.service
systemctl enable gtu-tunnel.service
systemctl enable gtu-watchdog.service

echo "--> [5/6] Starting all services now via systemd..."
systemctl restart gtu-postgres.service || true
sleep 2
systemctl restart gtu-portal.service || true
systemctl restart gtu-server-ui.service || true
systemctl restart gtu-tunnel.service || true
systemctl restart gtu-watchdog.service || true

echo ""
echo "Waiting 3 seconds for services to initialize..."
sleep 3

echo ""
echo "======================================================================"
echo " System Services Status:"
echo "======================================================================"
systemctl status gtu-postgres.service --no-pager | head -n 8 || true
echo "----------------------------------------------------------------------"
systemctl status gtu-portal.service --no-pager | head -n 8 || true
echo "----------------------------------------------------------------------"
systemctl status gtu-server-ui.service --no-pager | head -n 8 || true
echo "----------------------------------------------------------------------"
systemctl status gtu-tunnel.service --no-pager | head -n 8 || true
echo "----------------------------------------------------------------------"
systemctl status gtu-watchdog.service --no-pager | head -n 8 || true

echo ""
echo "======================================================================"
echo " [SUCCESS] 24/7 Permanent Auto-Start & Watchdog Guardian Configured!"
echo ""
echo " 🛡️ Bulletproof Features Active:"
echo "   1. Linux Systemd Services: Auto-starts on server boot / power cut."
echo "   2. Self-Healing Watchdog: Agar koi process crash hua toh turant restart karega."
echo "   3. User Lingering Enabled: Terminal / SSH band karne par bhi band NAHI hoga."
echo ""
echo " Live Links:"
echo "   - Server Web Console: https://gtu-itr-server.aceglory.in"
echo "   - IIC Portal:         https://iic-gtu-itr.aceglory.in"
echo "======================================================================"
