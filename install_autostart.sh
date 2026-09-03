#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Server & Portal - 1-Click Permanent Auto-Start on Machine Boot
# ==============================================================================
set -e

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Please run this script with sudo: sudo bash install_autostart.sh"
  exit 1
fi

PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
SERVER_UI_DIR="/home/gtu-itr/gtu-server-ui"

PORTAL_SRC="$PROJECT_DIR/gtu-portal.service"
SERVER_UI_SRC="$SERVER_UI_DIR/gtu-server-ui.service"
TUNNEL_SRC="$PROJECT_DIR/gtu-tunnel.service"

PORTAL_DEST="/etc/systemd/system/gtu-portal.service"
SERVER_UI_DEST="/etc/systemd/system/gtu-server-ui.service"
TUNNEL_DEST="/etc/systemd/system/gtu-tunnel.service"

echo "======================================================================"
echo " Setting up Permanent Auto-Start on Server Boot (Power Cut Resilient)"
echo " 1. Portal Web App:  https://iic-gtu-itr.aceglory.in  (Port 5000)"
echo " 2. Server Console:  https://gtu-itr-server.aceglory.in (Port 7000)"
echo "======================================================================"

echo ""
echo "--> [1/5] Stopping any manual background instances..."
pkill -f "gunicorn.*wsgi:app" 2>/dev/null || true
pkill -f "gunicorn.*gtu-server-ui" 2>/dev/null || true
pkill -f "cloudflared.*tunnel run" 2>/dev/null || true

echo "--> [2/5] Installing systemd service units to /etc/systemd/system/..."
cp "$PORTAL_SRC" "$PORTAL_DEST"
cp "$SERVER_UI_SRC" "$SERVER_UI_DEST"
cp "$TUNNEL_SRC" "$TUNNEL_DEST"
chmod 644 "$PORTAL_DEST" "$SERVER_UI_DEST" "$TUNNEL_DEST"

echo "--> [3/5] Reloading systemd daemon..."
systemctl daemon-reload

echo "--> [4/5] Enabling services to AUTO-START on machine boot..."
systemctl enable gtu-portal.service
systemctl enable gtu-server-ui.service
systemctl enable gtu-tunnel.service

echo "--> [5/5] Starting all services now..."
systemctl restart gtu-portal.service
systemctl restart gtu-server-ui.service
systemctl restart gtu-tunnel.service

echo ""
echo "Waiting 3 seconds for services to initialize..."
sleep 3

echo ""
echo "======================================================================"
echo " System Services Status:"
echo "======================================================================"
systemctl status gtu-portal.service --no-pager | head -n 12 || true
echo "----------------------------------------------------------------------"
systemctl status gtu-server-ui.service --no-pager | head -n 12 || true
echo "----------------------------------------------------------------------"
systemctl status gtu-tunnel.service --no-pager | head -n 12 || true

echo ""
echo "======================================================================"
echo " [SUCCESS] Permanent Auto-Start Configured Successfully!"
echo ""
echo " Both the Portal and Server Console are now running as Linux System Services."
echo " Power-Cut Resilient: Agar machine restart ya power cut hogi, toh boot"
echo " hote hi saari services automatically chalu ho jayengi!"
echo ""
echo " Live Links:"
echo "   - Server Web Console: https://gtu-itr-server.aceglory.in"
echo "   - IIC Portal:         https://iic-gtu-itr.aceglory.in"
echo "======================================================================"
