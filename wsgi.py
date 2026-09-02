import os
from app import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

# Default to production configuration in WSGI environment
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
