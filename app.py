"""
GTU-ITR R&D & IIC Portal - Main Application
"""
import os
import click
from datetime import date, timedelta
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()


def create_app(config_name=None):
    """Application factory."""
    app = Flask(__name__)

    # Load config
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    from config import config as config_dict
    app.config.from_object(config_dict.get(config_name, config_dict['default']))

    # Ensure required directories exist
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('EXPORT_FOLDER', 'exports'), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)

    # Auto-create MySQL database if configured
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('mysql'):
        try:
            from sqlalchemy.engine.url import make_url
            import pymysql
            import urllib.parse

            url = make_url(db_uri)
            # URL unquote password in case it is URL-encoded
            decoded_password = urllib.parse.unquote(url.password or '')

            # Connect to MySQL server without database
            connection = pymysql.connect(
                host=url.host or 'localhost',
                user=url.username or 'root',
                password=decoded_password,
                port=url.port or 3306,
                charset='utf8mb4'
            )
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{url.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                connection.commit()
            finally:
                connection.close()
        except Exception as e:
            app.logger.warning(f"Could not auto-create MySQL database: {e}")

    # Initialize extensions
    from extensions import db, login_manager, mail, migrate, csrf
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import models (registers them with SQLAlchemy)
    with app.app_context():
        import models  # noqa: F401

    # User loader for Flask-Login
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    from routes import register_blueprints
    register_blueprints(app)

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    @app.after_request
    def add_security_headers(response):
        """Inject secure response headers for legal/security compliance."""
        # Content Security Policy (CSP): Allow self, Google Fonts, Lucide icons (unpkg.com), Chart.js (jsdelivr)
        csp_policies = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' unpkg.com cdn.jsdelivr.net blob:",
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com",
            "font-src 'self' fonts.gstatic.com unpkg.com",
            "img-src 'self' data: blob:",
            "connect-src 'self'",
            "frame-ancestors 'self'"
        ]
        response.headers['Content-Security-Policy'] = "; ".join(csp_policies)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Strict-Transport-Security (HSTS) - enforce HTTPS in production
        if not app.debug and not app.testing:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
        return response

    # Template context processors
    @app.context_processor
    def inject_globals():
        from models.user import ROLE_LABELS
        return dict(
            role_labels=ROLE_LABELS,
            current_year=date.today().year,
        )

    # CLI Commands
    register_cli(app)

    return app


def register_cli(app):
    """Register CLI commands."""
    from extensions import db

    @app.cli.command('init-db')
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo('[OK] Database tables created.')

    @app.cli.command('seed-db')
    def seed_db():
        """Seed database with sample data."""
        from models.user import User
        from models.department import Department

        # Departments
        departments = [
            Department(name='Computer Engineering', code='CE', hod_name='Dr. Rajesh Patel'),
            Department(name='Information Technology', code='IT', hod_name='Dr. Priya Shah'),
            Department(name='Mechanical Engineering', code='ME', hod_name='Dr. Amit Kumar'),
            Department(name='Civil Engineering', code='CIV', hod_name='Dr. Suresh Joshi'),
            Department(name='Electrical Engineering', code='EE', hod_name='Dr. Neha Gupta'),
            Department(name='Electronics & Communication', code='EC', hod_name='Dr. Vikram Singh'),
        ]
        for dept in departments:
            existing = Department.query.filter_by(code=dept.code).first()
            if not existing:
                db.session.add(dept)

        db.session.commit()
        click.echo('[OK] Departments seeded.')

        # Users
        ce_dept = Department.query.filter_by(code='CE').first()
        it_dept = Department.query.filter_by(code='IT').first()
        me_dept = Department.query.filter_by(code='ME').first()

        users_data = [
            ('principal@gtu.ac.in', 'Principal User', 'PRINCIPAL', None, 'Principal'),
            ('chairperson@gtu.ac.in', 'Dr. IIC Chairperson', 'CHAIRPERSON', ce_dept.id, 'IIC Chairperson'),
            ('rdcoord@gtu.ac.in', 'Dr. R&D Coordinator', 'RD_COORDINATOR', it_dept.id, 'R&D Coordinator'),
            ('hod.ce@gtu.ac.in', 'Dr. CE HOD', 'HOD', ce_dept.id, 'HOD'),
            ('faculty.ce@gtu.ac.in', 'Prof. Arun Mehta', 'FACULTY', ce_dept.id, 'Assistant Professor'),
            ('faculty.it@gtu.ac.in', 'Prof. Sneha Desai', 'FACULTY', it_dept.id, 'Associate Professor'),
            ('student@gtu.ac.in', 'Rahul Student', 'STUDENT_REP', ce_dept.id, 'Student Rep'),
        ]
        for email, name, role, dept_id, desig in users_data:
            existing = User.query.filter_by(email=email).first()
            if not existing:
                u = User(email=email, full_name=name, role=role, department_id=dept_id, designation=desig)
                u.set_password('password123')
                db.session.add(u)

        db.session.commit()
        click.echo('[OK] Users seeded. (Default password: password123)')

        # No additional seeding required

        click.echo('\n[SUCCESS] All sample data seeded successfully!')


# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
