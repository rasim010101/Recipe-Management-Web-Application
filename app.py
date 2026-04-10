# app.py — готовый исправленный файл
import os
import re
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from difflib import get_close_matches

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

# локальные модели/blueprints
from entities import db, User, Recipe, Category, Favorite, Rating, Comment
# auth blueprint должен быть в файле auth.py и использовать blueprint bp
# мы импортируем и регистрируем ниже, чтобы avoid circular imports

# ----- конфигурация путей -----
BASEDIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASEDIR, 'instance')
DB_FILE = os.path.join(INSTANCE_DIR, 'recipes.sqlite')
UPLOAD_FOLDER = os.path.join(BASEDIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB

# убедимся, что instance и upload папки существуют (до любых операций с файлами)
Path(INSTANCE_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


def create_app():
    """Factory: создаёт и возвращает Flask app. Подходит для flask CLI и для запуска."""
    app = Flask(__name__, template_folder='templates', instance_path=INSTANCE_DIR, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

    # init extensions
    db.init_app(app)
    Migrate(app, db)

    # Login manager init
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # user_loader
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # register auth blueprint (if exists)
    try:
        from auth import bp as auth_bp
        app.register_blueprint(auth_bp)
    except Exception as e:
        # если blueprint отсутствует или импорт падает — выводим предупреждение, но приложение запускается
        print("Warning: auth blueprint not registered:", e)

    return app


app = create_app()

# -----------------------
# Утилиты (файлы, нормализация)
# -----------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(storage):
    if not storage or storage.filename == '':
        return None
    if not allowed_file(storage.filename):
        return None
    filename = secure_filename(storage.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    new_name = f"{uuid4().hex}.{ext}"
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], new_name)
    storage.save(abs_path)
    # возвращаем путь, который используется в шаблоне: /static/uploads/...
    rel = os.path.join('static', 'uploads', new_name).replace('\\', '/')
    return rel


def remove_file(rel_path):
    """Удаляет файл по относительному пути вида 'static/uploads/xxxx.png'."""
    if not rel_path:
        return
    try:
        abs_path = os.path.join(BASEDIR, rel_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except Exception:
        pass


def singularize(word: str) -> str:
    w = word.lower().strip()
    if w.endswith('s') and len(w) > 1:
        return w[:-1]
    return w


def tokenize_phrase(phrase: str) -> list:
    parts = re.split(r'[\s\-]+', phrase.strip().lower())
    return [singularize(p) for p in parts if p]


def normalize_ingredients(text: str) -> list:
    if not text:
        return []
    raw = [i.strip() for i in text.split(',') if i.strip()]
    out = []
    seen = set()
    for r in raw:
        tokens = tokenize_phrase(r)
        if tokens:
            joined = ' '.join(tokens)
            if joined not in seen:
                out.append(joined)
                seen.add(joined)
    return out


def find_best_matches(recipe_ings: list, user_ings: list, fuzzy_cutoff=0.75):
    matched = []
    user_set = set(user_ings)
    user_tokens_map = {u: set(tokenize_phrase(u)) for u in user_ings}
    for rec in recipe_ings:
        if rec in user_set:
            matched.append((rec, rec, 'exact'))
            continue
        rec_tokens = set(tokenize_phrase(rec))
        partial = None
        for u, utoks in user_tokens_map.items():
            if rec_tokens & utoks:
                partial = u
                break
        if partial:
            matched.append((rec, partial, 'partial'))
            continue
        candidates = get_close_matches(rec, user_ings, n=1, cutoff=fuzzy_cutoff) if user_ings else []
        if candidates:
            matched.append((rec, candidates[0], 'fuzzy'))
            continue
        matched.append((rec, None, 'none'))
    return matched


# -----------------------
# Маршруты — endpoint'ы с осмысленными именами
# -----------------------
def get_favorited_ids():
    """Returns a set of recipe IDs favorited by the current user."""
    if current_user.is_authenticated:
        rows = Favorite.query.filter_by(user_id=current_user.id).all()
        return {f.recipe_id for f in rows}
    return set()


@app.route('/')
def index():
    cats = Category.query.all()
    recipes = Recipe.query.filter_by(is_deleted=False).order_by(Recipe.created_at.desc()).all()
    return render_template('index.html', categories=cats, recipes=recipes, favorited_ids=get_favorited_ids())


@app.route('/recipes')
def all_recipes():
    cats = Category.query.all()
    cat_id = request.args.get('cat', type=int)
    q = Recipe.query.filter_by(is_deleted=False)
    if cat_id:
        q = q.filter_by(category_id=cat_id)
    recipes = q.order_by(Recipe.created_at.desc()).all()
    active_cat = cat_id
    return render_template('recipes_list.html', recipes=recipes, categories=cats, active_cat=active_cat, favorited_ids=get_favorited_ids())


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json() or request.form
    ing_text = data.get('ingredients', '')
    cat_id = data.get('category_id')
    title_query = data.get('title', '').strip()
    user_ing = normalize_ingredients(ing_text)
    q = Recipe.query.filter_by(is_deleted=False)
    if title_query:
        q = q.filter(Recipe.title.ilike(f'%{title_query}%'))
    if cat_id:
        try:
            q = q.filter_by(category_id=int(cat_id))
        except Exception:
            pass
    recipes = q.all()
    results = []

    # If no ingredients given — return all recipes in the selected category
    if not user_ing:
        for r in recipes:
            rec_ing = normalize_ingredients(r.ingredients)
            results.append({
                'id': r.id, 'title': r.title, 'ingredients': rec_ing,
                'image_path': r.image_path, 'match_count': len(rec_ing), 'total': len(rec_ing), 'score': 1.0
            })
        return jsonify(results)

    WEIGHTS = {'exact': 1.0, 'partial': 0.8, 'fuzzy': 0.5}
    for r in recipes:
        rec_ing = normalize_ingredients(r.ingredients)
        matched = find_best_matches(rec_ing, user_ing)
        match_count = sum(1 for _, _, t in matched if t in ('exact', 'partial', 'fuzzy'))
        if match_count == 0:
            continue
        weighted = sum(WEIGHTS.get(t, 0.0) for _, _, t in matched)
        total = len(rec_ing) if rec_ing else 1
        score = round((weighted / total), 3)
        results.append({
            'id': r.id, 'title': r.title, 'ingredients': rec_ing,
            'image_path': r.image_path, 'match_count': match_count, 'total': total, 'score': score
        })
    results = sorted(results, key=lambda x: (x['match_count'], x['score']), reverse=True)
    return jsonify(results)


def recipe_avg_rating(recipe_id):
    avg = db.session.query(db.func.avg(Rating.value)).filter(Rating.recipe_id == recipe_id).scalar()
    count = Rating.query.filter_by(recipe_id=recipe_id).count()
    return (round(avg, 1) if avg else None), count


@app.route('/recipe/<int:recipe_id>')
def recipe_page(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    if r.is_deleted:
        return "Recipe not found", 404
    is_favorited = False
    user_rating = None
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first() is not None
        if r.author_id != current_user.id:
            ur = Rating.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
            user_rating = ur.value if ur else None
    avg_rating, rating_count = recipe_avg_rating(recipe_id)
    comments = Comment.query.filter_by(recipe_id=recipe_id).order_by(Comment.created_at.asc()).all()
    return render_template('recipe.html', recipe=r, is_favorited=is_favorited,
                           user_rating=user_rating, avg_rating=avg_rating,
                           rating_count=rating_count, comments=comments)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    cats = Category.query.all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        instructions = request.form.get('instructions', '').strip()
        cat = request.form.get('category') or None
        image = request.files.get('image')
        img_path = save_file(image) if image else None
        new = Recipe(title=title, ingredients=ingredients, instructions=instructions,
                     image_path=img_path, author_id=current_user.id,
                     category_id=int(cat) if cat else None)
        db.session.add(new)
        db.session.commit()
        flash('Recipe added', 'success')
        return redirect(url_for('recipe_page', recipe_id=new.id))
    return render_template('add_recipe.html', recipe=None, categories=cats)


@app.route('/edit/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    if (r.author_id != current_user.id) and (not current_user.is_admin()):
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    cats = Category.query.all()
    if request.method == 'POST':
        r.title = request.form.get('title', '').strip()
        r.ingredients = request.form.get('ingredients', '').strip()
        r.instructions = request.form.get('instructions', '').strip()
        cat = request.form.get('category') or None
        r.category_id = int(cat) if cat else None
        image = request.files.get('image')
        if image:
            newp = save_file(image)
            # удаляем старый файл (если относительный путь в db)
            if newp and r.image_path:
                remove_file(r.image_path)
            r.image_path = newp
        db.session.commit()
        flash('Saved', 'success')
        return redirect(url_for('recipe_page', recipe_id=r.id))
    return render_template('add_recipe.html', recipe=r, categories=cats)


@app.route('/delete/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    if (r.author_id != current_user.id) and (not current_user.is_admin()):
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    r.is_deleted = True
    r.deleted_at = datetime.utcnow()
    db.session.commit()
    flash('Recipe moved to trash', 'info')
    return redirect(url_for('index'))


@app.route('/trash')
@login_required
def trash():
    if current_user.is_admin():
        items = Recipe.query.filter_by(is_deleted=True).all()
    else:
        items = Recipe.query.filter_by(is_deleted=True, author_id=current_user.id).all()
    return render_template('trash.html', recipes=items)


@app.route('/trash/restore/<int:recipe_id>', methods=['POST'])
@login_required
def trash_restore(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    if (r.author_id != current_user.id) and (not current_user.is_admin()):
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    r.is_deleted = False
    r.deleted_at = None
    db.session.commit()
    flash('Restored', 'success')
    return redirect(url_for('trash'))


@app.route('/trash/permanent/<int:recipe_id>', methods=['POST'])
@login_required
def trash_permanent(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    if not current_user.is_admin():
        flash('Only admin can permanently delete recipes', 'danger')
        return redirect(url_for('index'))
    if r.image_path:
        remove_file(r.image_path)
    db.session.delete(r)
    db.session.commit()
    flash('Recipe permanently deleted', 'success')
    return redirect(url_for('trash'))


@app.route('/admin/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
def category_delete(cat_id):
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    c = Category.query.get_or_404(cat_id)
    # unlink recipes from this category
    Recipe.query.filter_by(category_id=cat_id).update({'category_id': None})
    db.session.delete(c)
    db.session.commit()
    flash('Category deleted', 'success')
    return redirect(url_for('categories'))


@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Please enter a name', 'warning')
            return redirect(url_for('categories'))
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        c = Category(name=name, slug=slug)
        db.session.add(c)
        db.session.commit()
        flash('Category added', 'success')
        return redirect(url_for('categories'))
    cats = Category.query.all()
    return render_template('categories.html', categories=cats)


# -----------------------
# Рейтинг рецептов
# -----------------------
@app.route('/recipe/<int:recipe_id>/rate', methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    r = Recipe.query.get_or_404(recipe_id)
    if r.author_id == current_user.id:
        return jsonify({'error': 'Cannot rate your own recipe'}), 403
    data = request.get_json() or {}
    value = data.get('value')
    if not isinstance(value, int) or not (1 <= value <= 5):
        return jsonify({'error': 'Invalid value'}), 400
    existing = Rating.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if existing:
        existing.value = value
    else:
        db.session.add(Rating(user_id=current_user.id, recipe_id=recipe_id, value=value))
    db.session.commit()
    avg, count = recipe_avg_rating(recipe_id)
    return jsonify({'avg': avg, 'count': count, 'user_rating': value})


# -----------------------
# Комментарии
# -----------------------
@app.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    Recipe.query.get_or_404(recipe_id)
    text = request.form.get('text', '').strip()
    if not text:
        flash('Comment cannot be empty', 'warning')
        return redirect(url_for('recipe_page', recipe_id=recipe_id))
    db.session.add(Comment(user_id=current_user.id, recipe_id=recipe_id, body=text))
    db.session.commit()
    return redirect(url_for('recipe_page', recipe_id=recipe_id) + '#comments')


@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    c = Comment.query.get_or_404(comment_id)
    if c.user_id != current_user.id and not current_user.is_admin():
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    recipe_id = c.recipe_id
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for('recipe_page', recipe_id=recipe_id) + '#comments')


# -----------------------
# Настройки профиля
# -----------------------
@app.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        if new_username and new_username != current_user.username:
            if User.query.filter_by(username=new_username).first():
                flash('Username is already taken', 'warning')
                return redirect(url_for('profile_settings'))
            current_user.username = new_username
        avatar = request.files.get('avatar')
        if avatar and avatar.filename:
            path = save_file(avatar)
            if path:
                if current_user.avatar_path:
                    remove_file(current_user.avatar_path)
                current_user.avatar_path = path
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect(url_for('profile', username=current_user.username))
    return render_template('profile_settings.html')


# -----------------------
# Избранное
# -----------------------
@app.route('/recipe/<int:recipe_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(recipe_id):
    Recipe.query.get_or_404(recipe_id)
    existing = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Removed from favorites', 'info')
    else:
        db.session.add(Favorite(user_id=current_user.id, recipe_id=recipe_id))
        db.session.commit()
        flash('Added to favorites', 'success')
    return redirect(url_for('recipe_page', recipe_id=recipe_id))


@app.route('/favorites')
@login_required
def favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()
    recipes = [f.recipe for f in favs if not f.recipe.is_deleted]
    return render_template('favorites.html', recipes=recipes)


# -----------------------
# Профиль пользователя
# -----------------------
@app.route('/user/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    recipes = Recipe.query.filter_by(author_id=user.id, is_deleted=False).order_by(Recipe.created_at.desc()).all()
    fav_count = Favorite.query.filter_by(user_id=user.id).count()
    recipe_ids = [r.id for r in recipes]
    if recipe_ids:
        avg_author = db.session.query(db.func.avg(Rating.value)).filter(Rating.recipe_id.in_(recipe_ids)).scalar()
        total_ratings = Rating.query.filter(Rating.recipe_id.in_(recipe_ids)).count()
        avg_author = round(avg_author, 1) if avg_author else None
    else:
        avg_author, total_ratings = None, 0
    return render_template('profile.html', profile_user=user, recipes=recipes, fav_count=fav_count,
                           avg_author=avg_author, total_ratings=total_ratings)


# -----------------------
# CLI helper: создать админа (flask create-admin)
# -----------------------
@app.cli.command("create-admin")
def create_admin():
    """Create default admin user: runs as `flask create-admin`"""
    with app.app_context():
        db.create_all()
        email = 'admin@example.com'
        if User.query.filter_by(email=email).first():
            print("Admin already exists:", email)
            return
        admin = User(email=email, username='admin', password_hash=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Created admin:", email, "password: admin123")


# -----------------------
# Никаких массовых create_all при импорте модуля!
# -----------------------
# Если хочешь инициализировать БД локально — используй:
#   flask create-admin
# или запусти интерактивно:
#   python -c "from app import app; from models import db; with app.app_context(): db.create_all()"

if __name__ == '__main__':
    # локальный запуск dev-сервера
    app.run(debug=True)
