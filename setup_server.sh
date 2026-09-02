#!/usr/bin/env bash
# ==============================================================================
# GTU-ITR R&D & IIC Portal - 1-Click Server Setup Script
# ==============================================================================
# This script sets up the full application on a fresh Ubuntu/Debian server/PC:
# 1. Installs system packages (Python3, venv, PostgreSQL, Git, curl)
# 2. Configures PostgreSQL (database & user)
# 3. Sets up Python virtual environment & installs dependencies
# 4. Generates production .env file
# 5. Initializes database tables & seeds default users (including Master Admin)
# 6. Sets up systemd service to run gunicorn on boot
# ==============================================================================

set -e

DB_NAME="iic_cell_gtu"
DB_USER="gtu_admin"
DB_PASS="44113290"
DB_PORT="5432"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "======================================================================"
echo "    GTU-ITR Portal - Complete Server Setup"
echo "    Project Path: $PROJECT_DIR"
echo "======================================================================"

# 1. Update and install system dependencies
echo ""
echo "--> [1/6] Installing system dependencies..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    git \
    curl

# 2. Start PostgreSQL and configure user & database
echo ""
echo "--> [2/6] Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo -u postgres psql -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN CREATE ROLE ${DB_USER} WITH LOGIN SUPERUSER PASSWORD '${DB_PASS}'; ELSE ALTER ROLE ${DB_USER} WITH PASSWORD '${DB_PASS}'; END IF; END \$\$;"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1 || \
(sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" && \
 sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};")

echo "    PostgreSQL user '${DB_USER}' and database '${DB_NAME}' ready."

# 3. Setup Python virtual environment
echo ""
echo "--> [3/6] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

if command -v uv &>/dev/null; then
    uv pip install -r requirements.txt --python ./venv/bin/python
else
    ./venv/bin/pip install --upgrade pip 2>/dev/null || true
    ./venv/bin/pip install -r requirements.txt
fi

# 4. Setup .env file
echo ""
echo "--> [4/6] Configuring environment variables (.env)..."
if [ ! -f ".env" ]; then
    SECRET_KEY_GEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat <<ENV_EOF > .env
# GTU-ITR R&D & IIC Portal - Environment Configuration
SECRET_KEY=${SECRET_KEY_GEN}
FLASK_ENV=production
FLASK_DEBUG=0

# Database
DATABASE_URL=postgresql+psycopg2://${DB_USER}:${DB_PASS}@localhost:${DB_PORT}/${DB_NAME}

# Email (SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@gtu.ac.in

# AI Model
AI_DEVICE=cpu
AI_MODEL_NAME=microsoft/Phi-3-mini-4k-instruct
ENV_EOF
    echo "    Generated new .env file."
else
    echo "    Existing .env found. Ensuring DATABASE_URL points to PostgreSQL..."
    if ! grep -q "postgresql+psycopg2" .env; then
        sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg2://'${DB_USER}':'${DB_PASS}'@localhost:'${DB_PORT}'/'${DB_NAME}'|g' .env
    fi
fi

# 5. Initialize database tables & seed initial accounts
echo ""
echo "--> [5/6] Initializing database tables and admin..."
./venv/bin/python setup_db.py

# 6. Setup Systemd Service
echo ""
echo "--> [6/6] Configuring systemd background service..."
SERVICE_PATH="/etc/systemd/system/gtu-portal.service"
CURRENT_USER=$(whoami)

sudo bash -c "cat <<SVC_EOF > ${SERVICE_PATH}
[Unit]
Description=GTU-ITR R&D & IIC Portal Flask App
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=\"PATH=${PROJECT_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin\"
ExecStart=${PROJECT_DIR}/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC_EOF"

sudo systemctl daemon-reload
sudo systemctl enable gtu-portal.service
sudo systemctl restart gtu-portal.service

echo ""
echo "======================================================================"
echo " [SUCCESS] Deployment Completed Successfully!"
echo "======================================================================"
echo " - Portal URL: http://localhost:5000"
echo " - Admin Login: admin@gmail.com"
echo " - Password:    ${DB_PASS}"
echo ""
echo " Service Commands:"
echo "   sudo systemctl status gtu-portal"
echo "   sudo systemctl restart gtu-portal"
echo "   sudo systemctl stop gtu-portal"
echo "======================================================================"
