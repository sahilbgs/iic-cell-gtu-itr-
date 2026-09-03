import os
from werkzeug.middleware.proxy_fix import ProxyFix

# Ensure PostgreSQL database is locked and permanent on this server
PG_DB_URL = "postgresql+psycopg2://gtu_admin:44113290@localhost:5432/iic_cell_gtu"
current_db = os.environ.get('DATABASE_URL', '')
if not current_db or 'sqlite' in current_db:
    os.environ['DATABASE_URL'] = PG_DB_URL

from app import create_app

# Default to production configuration in WSGI environment
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
