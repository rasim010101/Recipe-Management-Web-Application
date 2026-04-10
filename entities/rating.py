from datetime import datetime
from entities.extensions import db


class Rating(db.Model):
    __tablename__ = 'ratings'

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    value     = db.Column(db.Integer, nullable=False)  # 1–5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'recipe_id', name='uq_user_recipe_rating'),
        db.CheckConstraint('value >= 1 AND value <= 5', name='ck_rating_value'),
    )

    def __repr__(self):
        return f'<Rating user={self.user_id} recipe={self.recipe_id} value={self.value}>'
