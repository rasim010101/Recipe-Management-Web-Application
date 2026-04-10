import sqlite3, os, glob, time
from datetime import datetime

def ensure_columns(db_path):
    print("== Работаем с", db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(recipes);")
    cols = [r[1] for r in cur.fetchall()]
    print("  Текущие колонки:", cols)
    changed = False
    if 'image_path' not in cols:
        print("  Добавляю колонку image_path...")
        cur.execute("ALTER TABLE recipes ADD COLUMN image_path TEXT;")
        changed = True
    if 'created_at' not in cols:
        print("  Добавляю колонку created_at...")
        cur.execute("ALTER TABLE recipes ADD COLUMN created_at TEXT;")
        changed = True
    if changed:
        conn.commit()
    # Заполним created_at для пустых строк текущим временем
    cur.execute("PRAGMA table_info(recipes);")
    cols = [r[1] for r in cur.fetchall()]
    if 'created_at' in cols:
        cur.execute("UPDATE recipes SET created_at = ? WHERE created_at IS NULL OR created_at = ''", (datetime.utcnow().isoformat(),))
        conn.commit()
        print("  Заполнил пустые created_at текущим UTC временем.")
    conn.close()
    print("  Готово.\n")

# Найдём все файлы recipes.sqlite рекурсивно от текущей папки
found = glob.glob('**/recipes.sqlite', recursive=True)
if not found:
    print("Файлы recipes.sqlite не найдены в текущей папке и подпапках.")
else:
    for db in found:
        ensure_columns(db)
print("Выполнение скрипта завершено.")