import sqlite3
import glob


def migrate(db_path):
    print("Database:", db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(recipes);")
    cols = [r[1] for r in cur.fetchall()]

    if 'view_count' not in cols:
        cur.execute("ALTER TABLE recipes ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0;")
        conn.commit()
        print("  Added column view_count.")
    else:
        print("  Column view_count already exists.")

    conn.close()


found = glob.glob('**/recipes.sqlite', recursive=True)
if not found:
    print("recipes.sqlite not found. Run this script from the project folder.")
else:
    for db in found:
        migrate(db)

print("Done.")
