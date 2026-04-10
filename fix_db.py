"""
Запустить один раз: python fix_db.py
Исправляет даты в базе данных (конвертирует числовые timestamp -> строки ISO).
"""
import sqlite3
import os
from datetime import datetime

BASEDIR = os.path.abspath(os.path.dirname(__file__))
DB_PATHS = [
    os.path.join(BASEDIR, 'instance', 'recipes.sqlite'),
    os.path.join(BASEDIR, 'recipes.sqlite'),
]

def fix_datetime(val):
    if val is None:
        return datetime.utcnow().isoformat()
    if isinstance(val, (int, float)):
        return datetime.utcfromtimestamp(val).isoformat()
    if isinstance(val, str):
        return val
    return datetime.utcnow().isoformat()

def fix_db(path):
    if not os.path.exists(path):
        print(f"  Не найден: {path}")
        return
    print(f"  Обрабатываю: {path}")
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    # определяем какие колонки есть в таблице
    cur.execute("PRAGMA table_info(recipes)")
    cols = {row[1] for row in cur.fetchall()}

    select_cols = ['id', 'created_at']
    if 'updated_at' in cols:
        select_cols.append('updated_at')
    if 'deleted_at' in cols:
        select_cols.append('deleted_at')

    cur.execute(f"SELECT {', '.join(select_cols)} FROM recipes")
    for row in cur.fetchall():
        row_id = row[0]
        created_at = row[1]
        updated_at = row[select_cols.index('updated_at')] if 'updated_at' in cols else None
        deleted_at = row[select_cols.index('deleted_at')] if 'deleted_at' in cols else None

        updates = {'created_at': fix_datetime(created_at)}
        if 'updated_at' in cols:
            updates['updated_at'] = fix_datetime(updated_at)
        if 'deleted_at' in cols:
            updates['deleted_at'] = fix_datetime(deleted_at) if deleted_at is not None else None

        set_clause = ', '.join(f"{k}=?" for k in updates)
        cur.execute(f"UPDATE recipes SET {set_clause} WHERE id=?",
                    list(updates.values()) + [row_id])

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}

    if 'users' in tables:
        cur.execute("SELECT id, created_at FROM users")
        for row_id, created_at in cur.fetchall():
            cur.execute("UPDATE users SET created_at=? WHERE id=?", (fix_datetime(created_at), row_id))

    if 'favorites' in tables:
        cur.execute("SELECT id, created_at FROM favorites")
        for row_id, created_at in cur.fetchall():
            cur.execute("UPDATE favorites SET created_at=? WHERE id=?", (fix_datetime(created_at), row_id))

    conn.commit()
    conn.close()
    print(f"  Готово!")

if __name__ == '__main__':
    for p in DB_PATHS:
        fix_db(p)
    print("\nБаза исправлена. Теперь запусти: flask run")
