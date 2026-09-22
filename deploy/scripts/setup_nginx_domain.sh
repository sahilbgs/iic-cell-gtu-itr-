#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR Portal - Nginx Reverse Proxy & Custom Domain Setup Script
# ==============================================================================
# Uses Nginx to reverse proxy port 80/443 to Gunicorn (http://127.0.0.1:5000)
# and configures free SSL with Let's Encrypt (Certbot).
# ==============================================================================
set -e

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] Please run this script with sudo: sudo bash setup_nginx_domain.sh"
  exit 1
fi

echo "======================================================================"
echo "    GTU-ITR Portal - Connect Domain with Nginx Reverse Proxy"
echo "======================================================================"
echo ""

read -p "Enter your domain name (e.g. portal.example.com): " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo "[ERROR] Domain name cannot be empty."
    exit 1
fi

echo ""
echo "--> [1/4] Installing Nginx and Certbot..."
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx

echo "--> [2/4] Configuring Nginx reverse proxy for '$DOMAIN_NAME'..."
NGINX_CONF="/etc/nginx/sites-available/gtu-portal"

cat <<NGINX_EOF > "$NGINX_CONF"
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /static/ {
        alias /home/gtu-itr/iic-cell-gtu-itr-/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
NGINX_EOF

# Enable site
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/gtu-portal
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

echo "--> [3/4] Testing Nginx configuration and restarting..."
nginx -t
systemctl restart nginx
systemctl enable nginx

echo ""
echo "--> [4/4] Free SSL Certificate Setup (Let's Encrypt)..."
read -p "Do you want to configure free HTTPS (SSL) right now? (y/n): " SETUP_SSL

if [[ "$SETUP_SSL" =~ ^[Yy]$ ]]; then
    read -p "Enter your email address for SSL certificate alerts: " SSL_EMAIL
    certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos -m "$SSL_EMAIL" --redirect || {
        echo "[WARNING] Certbot automatic SSL setup encountered an issue."
        echo "Please verify your DNS A-Record for '$DOMAIN_NAME' points to this server's public IP before running certbot."
    }
fi

echo ""
echo "======================================================================"
echo " [SUCCESS] Nginx configured for http://$DOMAIN_NAME!"
echo " Both Nginx and the GTU Portal will start automatically on boot."
echo "======================================================================"
