from datetime import datetime
from entities.extensions import db
from entities.tag import recipe_tags


class Recipe(db.Model):
    __tablename__ = 'recipes'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=True)

    ingredients  = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)

    prep_time  = db.Column(db.Integer,    nullable=True)
    cook_time  = db.Column(db.Integer,    nullable=True)
    servings   = db.Column(db.Integer,    nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)

    image_path  = db.Column(db.String(512), nullable=True)
    author_id   = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    is_published = db.Column(db.Boolean, default=True,  nullable=False)
    is_deleted   = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at   = db.Column(db.DateTime, nullable=True)
    view_count   = db.Column(db.Integer,  default=0,    nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps              = db.relationship('RecipeStep',       backref='recipe', lazy='dynamic',
                                         order_by='RecipeStep.step_number',
                                         cascade='all, delete-orphan')
    recipe_ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy='dynamic',
                                         cascade='all, delete-orphan')
    tags               = db.relationship('Tag', secondary=recipe_tags,
                                         backref='recipes', lazy='subquery')
    favorites          = db.relationship('Favorite', backref='recipe', lazy='dynamic',
                                         cascade='all, delete-orphan')
    ratings            = db.relationship('Rating',   backref='recipe', lazy='dynamic',
                                         cascade='all, delete-orphan')
    comments           = db.relationship('Comment',  backref='recipe', lazy='dynamic',
                                         cascade='all, delete-orphan')

    @property
    def total_time(self):
        return (self.prep_time or 0) + (self.cook_time or 0)

    @property
    def avg_rating(self):
        from entities.extensions import db as _db
        from entities.rating import Rating
        avg = _db.session.query(_db.func.avg(Rating.value)).filter_by(recipe_id=self.id).scalar()
        return round(avg, 1) if avg else None

    def __repr__(self):
        return f'<Recipe {self.title}>'
