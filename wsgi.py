import os
from app import create_app

# Default to production configuration in WSGI environment
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)
