#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal - 1-Click Auto-Start on Server Boot Script
# ==============================================================================
set -e

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Please run this script with sudo: sudo bash install_autostart.sh"
  exit 1
fi

PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
SERVICE_SRC="$PROJECT_DIR/gtu-portal.service"
SERVICE_DEST="/etc/systemd/system/gtu-portal.service"

echo "======================================================================"
echo " Setting up Auto-Start on Server Boot for GTU-ITR Portal"
echo "======================================================================"

echo "--> [1/4] Installing systemd service unit..."
cp "$SERVICE_SRC" "$SERVICE_DEST"
chmod 644 "$SERVICE_DEST"

echo "--> [2/4] Reloading systemd daemon..."
systemctl daemon-reload

echo "--> [3/4] Enabling service to start automatically on system boot..."
systemctl enable gtu-portal.service

echo "--> [4/4] Starting gtu-portal service now..."
systemctl restart gtu-portal.service

echo ""
echo "Checking service status..."
sleep 2
systemctl status gtu-portal.service --no-pager

echo ""
echo "======================================================================"
echo " [SUCCESS] Auto-Start is now configured!"
echo " The portal will now automatically start every time the server powers on."
echo "======================================================================"
echo " Management Commands:"
echo "   sudo systemctl status gtu-portal   # Check status"
echo "   sudo systemctl restart gtu-portal  # Restart portal"
echo "   sudo systemctl stop gtu-portal     # Stop portal"
echo "   sudo journalctl -u gtu-portal -f   # View live logs"
echo "======================================================================"
