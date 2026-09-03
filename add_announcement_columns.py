"""
GTU-ITR Portal - Database Migration for Public Announcements & External Registration
Applies new columns to both SQLite local DB and configured SQLAlchemy database.
"""
import os
import sqlite3

basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_path = os.path.join(basedir, 'instance', 'gtu_portal.db')

if os.path.exists(sqlite_path):
    print(f"Checking SQLite database at: {sqlite_path}")
    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()
    cur.execute("PRAGMA table_info(principal_posts);")
    existing = [col[1] for col in cur.fetchall()]
    print(f"Columns in SQLite principal_posts: {existing}")

    if 'registration_deadline' not in existing:
        try:
            cur.execute("ALTER TABLE principal_posts ADD COLUMN registration_deadline DATETIME NULL;")
            print("[OK] Added registration_deadline to SQLite")
        except Exception as e:
            print(f"[NOTE] SQLite registration_deadline: {e}")

    if 'is_public' not in existing:
        try:
            cur.execute("ALTER TABLE principal_posts ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0;")
            print("[OK] Added is_public to SQLite")
        except Exception as e:
            print(f"[NOTE] SQLite is_public: {e}")

    if 'external_registration_url' not in existing:
        try:
            cur.execute("ALTER TABLE principal_posts ADD COLUMN external_registration_url VARCHAR(500) NULL;")
            print("[OK] Added external_registration_url to SQLite")
        except Exception as e:
            print(f"[NOTE] SQLite external_registration_url: {e}")

    con.commit()
    con.close()
    print("[SUCCESS] SQLite migration complete.")

# Also run through SQLAlchemy in case MySQL/Postgres is active
try:
    from app import create_app
    from extensions import db
    from sqlalchemy import text, inspect

    app = create_app()
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('principal_posts')]
            print(f"Columns in SQLAlchemy principal_posts: {existing_columns}")

            if 'registration_deadline' not in existing_columns:
                try:
                    db.session.execute(text("ALTER TABLE principal_posts ADD COLUMN registration_deadline DATETIME NULL;"))
                    db.session.commit()
                    print("[OK] Added registration_deadline via SQLAlchemy")
                except Exception as e:
                    db.session.rollback()
                    print(f"[NOTE] registration_deadline: {e}")

            if 'is_public' not in existing_columns:
                try:
                    db.session.execute(text("ALTER TABLE principal_posts ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0;"))
                    db.session.commit()
                    print("[OK] Added is_public via SQLAlchemy")
                except Exception as e:
                    db.session.rollback()
                    print(f"[NOTE] is_public: {e}")

            if 'external_registration_url' not in existing_columns:
                try:
                    db.session.execute(text("ALTER TABLE principal_posts ADD COLUMN external_registration_url VARCHAR(500) NULL;"))
                    db.session.commit()
                    print("[OK] Added external_registration_url via SQLAlchemy")
                except Exception as e:
                    db.session.rollback()
                    print(f"[NOTE] external_registration_url: {e}")
        except Exception as e:
            print(f"SQLAlchemy check note: {e}")
except Exception as e:
    print(f"App initialization note: {e}")

print("Migration script finished.")
