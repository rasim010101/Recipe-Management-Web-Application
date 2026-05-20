"""
Добавляет колонку view_count в таблицу recipes (если её нет).
Запускать ОДИН РАЗ:
  python add_view_count_col.py
"""
import sqlite3, glob

def migrate(db_path):
    print("== База данных:", db_path)
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    cur.execute("PRAGMA table_info(recipes);")
    cols = [r[1] for r in cur.fetchall()]

    if 'view_count' not in cols:
        cur.execute("ALTER TABLE recipes ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0;")
        conn.commit()
        print("  ✅ Добавлена колонка view_count.")
    else:
        print("  Колонка view_count уже существует — ничего не делаем.")

    conn.close()

found = glob.glob('**/recipes.sqlite', recursive=True)
if not found:
    print("Файл recipes.sqlite не найден. Запусти скрипт из папки проекта.")
else:
    for db in found:
        migrate(db)

print("Готово.")
