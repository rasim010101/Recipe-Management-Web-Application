"""
Добавляет колонки is_email_confirmed и email_confirmed_at в таблицу users.
Запускать ОДИН РАЗ:
  python add_email_confirm_cols.py

Существующие пользователи получат is_email_confirmed = 1 (уже подтверждены),
чтобы не потерять доступ к аккаунтам.
"""
import sqlite3, glob

def migrate(db_path):
    print("== База данных:", db_path)
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    cur.execute("PRAGMA table_info(users);")
    cols = [r[1] for r in cur.fetchall()]

    changed = False

    if 'is_email_confirmed' not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN is_email_confirmed BOOLEAN NOT NULL DEFAULT 0;")
        # Существующих пользователей сразу помечаем как подтверждённых
        cur.execute("UPDATE users SET is_email_confirmed = 1;")
        print("  ✅ Добавлена колонка is_email_confirmed (существующие пользователи = confirmed).")
        changed = True

    if 'email_confirmed_at' not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN email_confirmed_at DATETIME;")
        print("  ✅ Добавлена колонка email_confirmed_at.")
        changed = True

    if changed:
        conn.commit()
        print("  Изменения сохранены.")
    else:
        print("  Колонки уже существуют — ничего не делаем.")

    conn.close()

found = glob.glob('**/recipes.sqlite', recursive=True)
if not found:
    print("Файл recipes.sqlite не найден. Запусти скрипт из папки проекта.")
else:
    for db in found:
        migrate(db)

print("Готово.")
