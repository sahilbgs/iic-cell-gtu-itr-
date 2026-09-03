#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal - 1-Click Auto-Start & Domain Connection Script
# ==============================================================================
set -e

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Please run this script with sudo: sudo bash install_autostart.sh"
  exit 1
fi

PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
PORTAL_SRC="$PROJECT_DIR/gtu-portal.service"
TUNNEL_SRC="$PROJECT_DIR/gtu-tunnel.service"
PORTAL_DEST="/etc/systemd/system/gtu-portal.service"
TUNNEL_DEST="/etc/systemd/system/gtu-tunnel.service"

echo "======================================================================"
echo " Setting up Auto-Start on Server Boot for GTU-ITR Portal & Domain"
echo " Domain: https://iic-gtu-itr.aceglory.in"
echo "======================================================================"

echo ""
echo "--> [1/5] Installing systemd service units..."
cp "$PORTAL_SRC" "$PORTAL_DEST"
cp "$TUNNEL_SRC" "$TUNNEL_DEST"
chmod 644 "$PORTAL_DEST" "$TUNNEL_DEST"

echo "--> [2/5] Reloading systemd daemon..."
systemctl daemon-reload

echo "--> [3/5] Enabling services to auto-start on server boot..."
systemctl enable gtu-portal.service
systemctl enable gtu-tunnel.service

echo "--> [4/5] Starting gtu-portal (Flask/Gunicorn) service..."
systemctl restart gtu-portal.service

echo "--> [5/5] Starting gtu-tunnel (Cloudflare Tunnel) service..."
systemctl restart gtu-tunnel.service

echo ""
echo "Waiting 3 seconds for services to initialize..."
sleep 3

echo ""
echo "======================================================================"
echo " Service Status Check:"
echo "======================================================================"
systemctl status gtu-portal.service --no-pager || true
echo "----------------------------------------------------------------------"
systemctl status gtu-tunnel.service --no-pager || true

echo ""
echo "======================================================================"
echo " [SUCCESS] Deployment Completed!"
echo " 1. Portal Web App: http://localhost:5000"
echo " 2. Live Domain:    https://iic-gtu-itr.aceglory.in"
echo " 3. Server Auto-Start: ENABLED (Starts automatically on machine boot)"
echo "======================================================================"
echo " Management Commands:"
echo "   sudo systemctl status gtu-portal   # Web app status"
echo "   sudo systemctl status gtu-tunnel   # Tunnel status"
echo "   sudo journalctl -u gtu-portal -f   # Web app live logs"
echo "   sudo journalctl -u gtu-tunnel -f   # Tunnel live logs"
echo "   sudo systemctl restart gtu-portal  # Restart web app"
echo "   sudo systemctl restart gtu-tunnel  # Restart tunnel"
echo "======================================================================"
