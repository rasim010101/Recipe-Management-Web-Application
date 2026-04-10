"""
update_db.py — безопасно добавляет новые колонки и таблицы в существующую БД.
Запускать: python update_db.py
Можно запускать несколько раз — уже существующие колонки пропускаются.
"""
import sqlite3
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASEDIR, 'instance', 'recipes.sqlite')
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(BASEDIR, 'recipes.sqlite')

print(f"Database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


def existing_columns(table):
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def existing_tables():
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cur.fetchall()}


def add_column(table, column, col_type):
    if column not in existing_columns(table):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"  + {table}.{column}")
    else:
        print(f"  . {table}.{column} (already exists)")


tables = existing_tables()

# ── users ──────────────────────────────────────────────────────────────────
if 'users' in tables:
    print("\n[users]")
    add_column('users', 'bio',        'TEXT')
    add_column('users', 'avatar_path','VARCHAR(512)')
    add_column('users', 'is_active',  'BOOLEAN DEFAULT 1 NOT NULL')
    add_column('users', 'updated_at', 'DATETIME')

# ── categories ─────────────────────────────────────────────────────────────
if 'categories' in tables:
    print("\n[categories]")
    add_column('categories', 'description', 'VARCHAR(255)')
    add_column('categories', 'image_path',  'VARCHAR(512)')
    add_column('categories', 'created_at',  'DATETIME')

# ── recipes ────────────────────────────────────────────────────────────────
if 'recipes' in tables:
    print("\n[recipes]")
    add_column('recipes', 'description',  'VARCHAR(500)')
    add_column('recipes', 'prep_time',    'INTEGER')
    add_column('recipes', 'cook_time',    'INTEGER')
    add_column('recipes', 'servings',     'INTEGER')
    add_column('recipes', 'difficulty',   'VARCHAR(20)')
    add_column('recipes', 'is_published', 'BOOLEAN DEFAULT 1 NOT NULL')
    add_column('recipes', 'view_count',   'INTEGER DEFAULT 0 NOT NULL')
    add_column('recipes', 'updated_at',   'DATETIME')

# ── comments — rename text→body if needed ──────────────────────────────────
if 'comments' in tables:
    print("\n[comments]")
    cols = existing_columns('comments')
    if 'text' in cols and 'body' not in cols:
        cur.execute("""
            CREATE TABLE comments_new (
                id         INTEGER PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                recipe_id  INTEGER NOT NULL REFERENCES recipes(id),
                parent_id  INTEGER REFERENCES comments_new(id),
                body       TEXT NOT NULL,
                is_deleted BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME,
                updated_at DATETIME
            )
        """)
        cur.execute("""
            INSERT INTO comments_new (id, user_id, recipe_id, body, created_at)
            SELECT id, user_id, recipe_id, text, created_at FROM comments
        """)
        cur.execute("DROP TABLE comments")
        cur.execute("ALTER TABLE comments_new RENAME TO comments")
        print("  + comments rebuilt (text -> body, added parent_id, is_deleted, updated_at)")
    else:
        add_column('comments', 'parent_id',  'INTEGER REFERENCES comments(id)')
        add_column('comments', 'is_deleted', 'BOOLEAN DEFAULT 0 NOT NULL')
        add_column('comments', 'updated_at', 'DATETIME')
else:
    print("\n[comments] — creating")
    cur.execute("""
        CREATE TABLE comments (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            recipe_id  INTEGER NOT NULL REFERENCES recipes(id),
            parent_id  INTEGER REFERENCES comments(id),
            body       TEXT NOT NULL,
            is_deleted BOOLEAN DEFAULT 0 NOT NULL,
            created_at DATETIME,
            updated_at DATETIME
        )
    """)

# ── ratings ────────────────────────────────────────────────────────────────
if 'ratings' not in tables:
    print("\n[ratings] — creating")
    cur.execute("""
        CREATE TABLE ratings (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            recipe_id  INTEGER NOT NULL REFERENCES recipes(id),
            value      INTEGER NOT NULL CHECK(value >= 1 AND value <= 5),
            created_at DATETIME,
            UNIQUE(user_id, recipe_id)
        )
    """)
else:
    print("\n[ratings] already exists")
    add_column('ratings', 'created_at', 'DATETIME')

# ── favorites ──────────────────────────────────────────────────────────────
if 'favorites' not in tables:
    print("\n[favorites] — creating")
    cur.execute("""
        CREATE TABLE favorites (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            recipe_id  INTEGER NOT NULL REFERENCES recipes(id),
            created_at DATETIME,
            UNIQUE(user_id, recipe_id)
        )
    """)
else:
    print("\n[favorites] already exists")

# ── tags ───────────────────────────────────────────────────────────────────
if 'tags' not in tables:
    print("\n[tags] — creating")
    cur.execute("""
        CREATE TABLE tags (
            id   INTEGER PRIMARY KEY,
            name VARCHAR(80)  NOT NULL UNIQUE,
            slug VARCHAR(100) NOT NULL UNIQUE
        )
    """)

if 'recipe_tags' not in tables:
    cur.execute("""
        CREATE TABLE recipe_tags (
            recipe_id INTEGER NOT NULL REFERENCES recipes(id),
            tag_id    INTEGER NOT NULL REFERENCES tags(id),
            PRIMARY KEY (recipe_id, tag_id)
        )
    """)
    print("  + recipe_tags created")

# ── ingredients ────────────────────────────────────────────────────────────
if 'ingredients' not in tables:
    print("\n[ingredients] — creating")
    cur.execute("""
        CREATE TABLE ingredients (
            id           INTEGER PRIMARY KEY,
            name         VARCHAR(150) NOT NULL UNIQUE,
            default_unit VARCHAR(50)
        )
    """)

if 'recipe_ingredients' not in tables:
    cur.execute("""
        CREATE TABLE recipe_ingredients (
            id            INTEGER PRIMARY KEY,
            recipe_id     INTEGER NOT NULL REFERENCES recipes(id),
            ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
            amount        REAL,
            unit          VARCHAR(50),
            notes         VARCHAR(150),
            UNIQUE(recipe_id, ingredient_id)
        )
    """)
    print("  + recipe_ingredients created")

# ── recipe_steps ───────────────────────────────────────────────────────────
if 'recipe_steps' not in tables:
    print("\n[recipe_steps] — creating")
    cur.execute("""
        CREATE TABLE recipe_steps (
            id          INTEGER PRIMARY KEY,
            recipe_id   INTEGER NOT NULL REFERENCES recipes(id),
            step_number INTEGER NOT NULL,
            description TEXT    NOT NULL,
            image_path  VARCHAR(512),
            UNIQUE(recipe_id, step_number)
        )
    """)

conn.commit()
conn.close()
print("\nDone! Database updated successfully.")
print("Now run: flask run")
