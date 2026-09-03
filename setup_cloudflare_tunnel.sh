#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal - Cloudflare Tunnel Runner Script
# Domain: https://iic-gtu-itr.aceglory.in
# Tunnel: 0db9da8f-002e-4e4c-8f89-c5d548652de7
# ==============================================================================
set -e

PROJECT_DIR="/home/gtu-itr/iic-cell-gtu-itr-"
CLOUDFLARED="$PROJECT_DIR/venv/bin/cloudflared"
CONFIG_FILE="$PROJECT_DIR/.cloudflared/config.yml"
TUNNEL_ID="0db9da8f-002e-4e4c-8f89-c5d548652de7"

echo "======================================================================"
echo "    Starting Cloudflare Tunnel for https://iic-gtu-itr.aceglory.in"
echo "    Tunnel ID: $TUNNEL_ID"
echo "======================================================================"

exec "$CLOUDFLARED" --config "$CONFIG_FILE" tunnel run "$TUNNEL_ID"
