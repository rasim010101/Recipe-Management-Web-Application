# 🍳 RecipeHub

> **Diploma Project 2026** — Back-end Web Development  
> Student: Beknur Dzhaksybekov · Supervisor: Assoc. Prof. Dr. Isa Muslu

A full-stack recipe-sharing web application built with **Flask** and **SQLite**, featuring user authentication, intelligent ingredient-based search, ratings, favourites, and a modern responsive UI.

🌐 **Live demo:** `https://YOUR_USERNAME.pythonanywhere.com` _(replace with your PythonAnywhere URL)_  
📁 **Repository:** `https://github.com/YOUR_USERNAME/YOUR_REPO` _(replace with your GitHub URL)_

---

## ✨ Features

| Area | What it does |
|---|---|
| 🔐 **Auth** | Register, login, logout — PBKDF2-SHA256 password hashing, Flask-Login sessions |
| 🔍 **Smart Search** | SQL LIKE pre-filter + weighted fuzzy scoring by ingredient match percentage |
| 🍽 **Recipe CRUD** | Create, edit, soft-delete recipes with image upload (2 MB cap, PNG/JPG/GIF) |
| ⭐ **Ratings** | 1-5 star ratings per user via AJAX — no page reload |
| ♥ **Favourites** | Save/remove recipes to personal favourites list |
| 🗑 **Trash / Restore** | Soft delete with restore; hard-purge for admins |
| 💬 **Comments** | Nested comments on every recipe |
| 📂 **Categories** | Admin-managed category tags + category browsing grid |
| 📄 **Pagination** | 12 recipes per page with smart ellipsis navigation |
| 👤 **Profiles** | Avatar upload, bio, stats (recipes, favourites, avg rating) |
| ⚙ **Admin Panel** | User management (enable/disable), recipe oversight, platform stats |
| 🌑 **Search Overlay** | Global live search on every page — press **/** or click the search button |

---

## 🛠 Tech Stack

**Back-end**
- Python 3.10+ / Flask 3.x
- SQLAlchemy ORM + Flask-Migrate (Alembic)
- Flask-Login for session management
- Werkzeug for password hashing and file handling
- python-dotenv for environment variable management
- SQLite database (production-ready on PythonAnywhere)

**Front-end**
- Jinja2 templates with macros
- Bootstrap 5.3 + custom CSS design system (`static/css/main.css`)
- Inter font (Google Fonts)
- Vanilla JavaScript (Fetch API, debounced search, AJAX ratings, form validation)

**Design Patterns used**
- Application Factory (`create_app()`)
- Blueprint (`auth.py` — authentication module)
- Repository/ORM (SQLAlchemy models as data layer)
- Soft Delete (is_deleted flag, trash/restore flow)
- Observer-like (Flask signals via Flask-Login)

---

## 📁 Project Structure

```
backend_ready/
├── app.py                  # Main application — routes, factory
├── auth.py                 # Auth Blueprint (register/login/logout)
├── entities/               # SQLAlchemy models
│   ├── __init__.py         # db + all model exports
│   ├── user.py             # User model
│   ├── recipe.py           # Recipe model
│   ├── category.py         # Category model
│   ├── rating.py           # Rating model
│   ├── comment.py          # Comment model
│   ├── favorite.py         # Favourite model
│   ├── ingredient.py       # Ingredient model
│   ├── recipe_ingredient.py
│   ├── recipe_step.py
│   └── tag.py
├── templates/
│   ├── base.html           # Base layout (navbar, search overlay, footer)
│   ├── index.html          # Landing page (hero, categories, latest, top rated)
│   ├── recipes_list.html   # Recipe catalog with filters & pagination
│   ├── recipe.html         # Single recipe page with sidebar
│   ├── add_recipe.html     # Add/edit recipe form with image preview
│   ├── profile.html        # User profile page
│   ├── profile_settings.html
│   ├── login.html
│   ├── register.html
│   ├── admin.html
│   ├── favorites.html
│   ├── trash.html
│   ├── categories.html
│   └── _pagination.html    # Reusable pagination macro
├── static/
│   ├── css/main.css        # Full custom design system
│   └── uploads/            # User-uploaded images (git-ignored)
├── instance/               # SQLite database (git-ignored)
├── migrations/             # Alembic migration scripts
├── .env                    # Secret keys (git-ignored)
├── .gitignore
├── init_db.py              # DB init helper
└── requirements.txt
```

---

## 🚀 Local Setup

### 1. Clone & enter the project

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file in the project root:

```env
SECRET_KEY=your-random-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=1
```

Generate a good secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialise the database

```bash
flask db upgrade
# or, first time only:
python init_db.py
```

### 6. Run the development server

```bash
flask run
```

Open **http://127.0.0.1:5000** in your browser.

---

## 🌐 Deployment (PythonAnywhere)

1. Upload all project files (or `git clone` in PythonAnywhere console)
2. Create a virtual environment and install `requirements.txt`
3. In **Web** tab → add a new web app → Manual configuration → Python 3.10
4. Set the WSGI file path to your project's `wsgi.py` (or edit the generated one):

```python
import sys
sys.path.insert(0, '/home/YOUR_USERNAME/YOUR_REPO')

from app import app as application
```

5. Set environment variables in the PythonAnywhere **Web** tab → "Environment variables" section (or use a `.env` file)
6. Reload the web app

Live URL: `https://YOUR_USERNAME.pythonanywhere.com`

---

## 📸 Screenshots

> _Add screenshots of the running application here_

| Page | Preview |
|---|---|
| 🏠 Landing page | _(screenshot)_ |
| 🍽 Recipe catalog | _(screenshot)_ |
| 📖 Recipe page | _(screenshot)_ |
| 🔍 Search overlay | _(screenshot)_ |
| 👤 Profile page | _(screenshot)_ |
| ⚙ Admin panel | _(screenshot)_ |

---

## 🗄 Database Schema

11 models across these core entities:

```
User ──< Recipe ──< RecipeIngredient >── Ingredient
          │    ──< RecipeStep
          │    ──< Rating
          │    ──< Comment
          │    ──> Category
          │
User ──< Favorite >── Recipe
User ──< Rating  >── Recipe
```

Key design decisions:
- **Soft delete** on recipes: `is_deleted` flag, `deleted_at` timestamp
- **Cascading** deletes for comments, ratings, and favourites when a recipe is hard-purged
- **Avatar + image paths** stored as relative paths; files live in `static/uploads/`

---

## 🔑 Key Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/recipes` | Recipe catalog (paginated, sortable, filterable) |
| POST | `/search` | JSON search API (returns scored results) |
| GET | `/recipe/<id>` | Recipe detail page |
| GET/POST | `/add` | Add new recipe |
| GET/POST | `/recipe/<id>/edit` | Edit recipe |
| POST | `/recipe/<id>/delete` | Soft-delete recipe |
| POST | `/recipe/<id>/rate` | Rate a recipe (AJAX) |
| POST | `/recipe/<id>/favorite` | Toggle favourite (AJAX) |
| GET | `/profile/<username>` | User profile |
| GET/POST | `/settings` | Profile settings |
| GET | `/favorites` | My favourites |
| GET | `/trash` | Deleted recipes |
| GET | `/admin` | Admin panel |
| GET | `/auth/login` | Login |
| GET | `/auth/register` | Register |
| GET | `/auth/logout` | Logout |

---

## 📦 Requirements

```
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-Login
Werkzeug
python-dotenv
```

Install: `pip install -r requirements.txt`

---

## 📝 License

Academic use only — Diploma Project 2026.
