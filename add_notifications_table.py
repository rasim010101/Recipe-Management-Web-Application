"""
Создаёт таблицу notifications если её ещё нет.
Запускать ОДИН РАЗ на сервере:
  python add_notifications_table.py
"""
import sqlite3, os, glob

def add_notifications_table(db_path):
    print("== База данных:", db_path)
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # Проверяем, есть ли уже таблица
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications';")
    if cur.fetchone():
        print("  Таблица notifications уже существует — ничего не делаем.")
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
    print("  ✅ Таблица notifications создана.")
    conn.close()

# Ищем recipes.sqlite в текущей папке и подпапках
found = glob.glob('**/recipes.sqlite', recursive=True)
if not found:
    print("Файл recipes.sqlite не найден. Запусти скрипт из папки проекта.")
else:
    for db in found:
        add_notifications_table(db)

print("Готово.")
