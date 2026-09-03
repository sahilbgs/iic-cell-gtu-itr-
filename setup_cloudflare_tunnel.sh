#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal - Cloudflare Tunnel Domain Connection Script
# ==============================================================================
# Connects your domain to http://localhost:5000 securely without needing:
# - A static public IP
# - Port forwarding on college/institutional routers
# - Manual SSL certificates (Cloudflare handles HTTPS automatically)
# ==============================================================================
set -e

echo "======================================================================"
echo "    GTU-ITR Portal - Connect Custom Domain via Cloudflare Tunnel"
echo "======================================================================"
echo ""

# 1. Check if cloudflared is installed
if ! command -v cloudflared &>/dev/null; then
    echo "--> [1/3] Downloading & installing cloudflared..."
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i /tmp/cloudflared.deb || sudo apt-get install -f -y
    rm -f /tmp/cloudflared.deb
    echo "    [OK] cloudflared installed."
else
    echo "--> [1/3] cloudflared is already installed."
fi

echo ""
echo "--> [2/3] How would you like to connect your domain?"
echo "    Option A: Cloudflare Dashboard Token (RECOMMENDED - 1 Click)"
echo "              1. Go to https://one.dash.cloudflare.com -> Networks -> Tunnels"
echo "              2. Create a tunnel -> Name it 'gtu-portal' -> Select Debian/Ubuntu"
echo "              3. Copy the token command provided by Cloudflare"
echo "              4. Point your domain (e.g. portal.yourdomain.com) to http://localhost:5000"
echo ""
echo "    Option B: Quick Temporary URL (instant test without domain setup)"
echo ""

read -p "Enter your Cloudflare Tunnel Token (or press Enter to run a quick test tunnel): " TUNNEL_TOKEN

if [ -n "$TUNNEL_TOKEN" ]; then
    echo ""
    echo "--> [3/3] Installing Cloudflare Tunnel as an auto-start background service..."
    sudo cloudflared service install "$TUNNEL_TOKEN"
    sudo systemctl enable cloudflared
    sudo systemctl restart cloudflared
    echo ""
    echo "======================================================================"
    echo " [SUCCESS] Cloudflare Tunnel is active and configured to start on boot!"
    echo " Your domain is now securely connected to the GTU-ITR Portal!"
    echo "======================================================================"
else
    echo ""
    echo "--> Starting a quick temporary tunnel to http://localhost:5000..."
    echo "    (Press Ctrl+C anytime to stop)"
    cloudflared tunnel --url http://localhost:5000
fi
