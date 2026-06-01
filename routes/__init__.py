"""
GTU-ITR R&D & IIC Portal - Routes Package
Registers all Blueprints with the Flask application.
"""


def register_blueprints(app):
    """Import and register every blueprint with the Flask app."""
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.posts import posts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(posts_bp)
