from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add is_deleted to users table
        db.session.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0;"))
        print("Added is_deleted to users")
    except Exception as e:
        print(f"users table: {e}")
        
    try:
        # Add is_deleted to departments table
        db.session.execute(text("ALTER TABLE departments ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0;"))
        print("Added is_deleted to departments")
    except Exception as e:
        print(f"departments table: {e}")
        
    try:
        # Add is_deleted to landing_posts table
        db.session.execute(text("ALTER TABLE landing_posts ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0;"))
        print("Added is_deleted to landing_posts")
    except Exception as e:
        print(f"landing_posts table: {e}")
        
    db.session.commit()
    print("Done")
