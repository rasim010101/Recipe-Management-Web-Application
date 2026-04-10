"""
Run once: python update_db.py
Adds new tables (ratings, comments) and avatar_path column to users.
"""
import sqlite3
import os
from datetime import datetime

BASEDIR = os.path.abspath(os.path.dirname(__file__))
DB_PATHS = [
    os.path.join(BASEDIR, 'instance', 'recipes.sqlite'),
    os.path.join(BASEDIR, 'recipes.sqlite'),
]

def update_db(path):
    if not os.path.exists(path):
        print(f"  Not found: {path}")
        return
    print(f"  Processing: {path}")
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    # Add avatar_path to users if missing
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cur.fetchone():
        cur.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if 'avatar_path' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN avatar_path VARCHAR(512)")
            print("  + Added avatar_path to users")

    # Create ratings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            recipe_id INTEGER NOT NULL REFERENCES recipes(id),
            value INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, recipe_id)
        )
    """)
    print("  + ratings table ready")

    # Create comments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            recipe_id INTEGER NOT NULL REFERENCES recipes(id),
            text TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  + comments table ready")

    conn.commit()
    conn.close()
    print(f"  Done!")

if __name__ == '__main__':
    for p in DB_PATHS:
        update_db(p)
    print("\nDatabase updated. Now run: flask run")
