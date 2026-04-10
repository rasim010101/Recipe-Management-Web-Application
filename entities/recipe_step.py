from entities.extensions import db


class RecipeStep(db.Model):
    """One numbered step of a recipe's instructions."""
    __tablename__ = 'recipe_steps'

    id          = db.Column(db.Integer, primary_key=True)
    recipe_id   = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path  = db.Column(db.String(512), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('recipe_id', 'step_number', name='uq_recipe_step'),
    )

    def __repr__(self):
        return f'<RecipeStep recipe={self.recipe_id} step={self.step_number}>'
