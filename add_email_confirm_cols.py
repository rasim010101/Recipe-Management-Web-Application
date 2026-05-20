import sqlite3
import glob


def migrate(db_path):
    print("Database:", db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(users);")
    cols = [r[1] for r in cur.fetchall()]

    changed = False

    if 'is_email_confirmed' not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN is_email_confirmed BOOLEAN NOT NULL DEFAULT 0;")
        cur.execute("UPDATE users SET is_email_confirmed = 1;")
        print("  Added column is_email_confirmed.")
        changed = True

    if 'email_confirmed_at' not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN email_confirmed_at DATETIME;")
        print("  Added column email_confirmed_at.")
        changed = True

    if changed:
        conn.commit()
        print("  Changes saved.")
    else:
        print("  Columns already exist.")

    conn.close()


found = glob.glob('**/recipes.sqlite', recursive=True)
if not found:
    print("recipes.sqlite not found. Run this script from the project folder.")
else:
    for db in found:
        migrate(db)

print("Done.")
