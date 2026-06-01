"""
GTU-ITR R&D & IIC Portal - Flask Extensions
Initialized here to avoid circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Database
db = SQLAlchemy()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Email
mail = Mail()

# Database Migrations
migrate = Migrate()

# CSRF Protection
csrf = CSRFProtect()
