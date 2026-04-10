from entities.extensions import db


class RecipeIngredient(db.Model):
    """Junction: Recipe ↔ Ingredient with amount, unit, and optional notes."""
    __tablename__ = 'recipe_ingredients'

    id            = db.Column(db.Integer, primary_key=True)
    recipe_id     = db.Column(db.Integer, db.ForeignKey('recipes.id'),     nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    amount        = db.Column(db.Float,      nullable=True)   # e.g. 200
    unit          = db.Column(db.String(50), nullable=True)   # e.g. 'g', 'tbsp'
    notes         = db.Column(db.String(150), nullable=True)  # e.g. 'finely chopped'

    __table_args__ = (
        db.UniqueConstraint('recipe_id', 'ingredient_id', name='uq_recipe_ingredient'),
    )

    def __repr__(self):
        return f'<RecipeIngredient recipe={self.recipe_id} ingredient={self.ingredient_id}>'
