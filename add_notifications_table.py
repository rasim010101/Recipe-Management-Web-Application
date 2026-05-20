import sqlite3
import glob


def add_notifications_table(db_path):
    print("Database:", db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications';")
    if cur.fetchone():
        print("  Table notifications already exists.")
        conn.close()
        return

    cur.execute("""
        CREATE TABLE notifications (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            from_user_id INTEGER REFERENCES users(id),
            recipe_id    INTEGER REFERENCES recipes(id),
            type         VARCHAR(20) NOT NULL,
            message      VARCHAR(255) NOT NULL,
            is_read      BOOLEAN NOT NULL DEFAULT 0,
            created_at   DATETIME DEFAULT (datetime('now'))
        );
    """)
    cur.execute("CREATE INDEX ix_notifications_user_id ON notifications(user_id);")
    cur.execute("CREATE INDEX ix_notifications_is_read ON notifications(is_read);")
    conn.commit()
    print("  Table notifications created.")
    conn.close()


found = glob.glob('**/recipes.sqlite', recursive=True)
if not found:
    print("recipes.sqlite not found. Run this script from the project folder.")
else:
    for db in found:
        add_notifications_table(db)

print("Done.")
