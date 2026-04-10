from entities.extensions import db


class Ingredient(db.Model):
    """Lookup table of canonical ingredients."""
    __tablename__ = 'ingredients'

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(150), unique=True, nullable=False)
    default_unit = db.Column(db.String(50),  nullable=True)  # e.g. 'g', 'ml', 'pcs'

    recipe_ingredients = db.relationship('RecipeIngredient', backref='ingredient', lazy='dynamic')

    def __repr__(self):
        return f'<Ingredient {self.name}>'
