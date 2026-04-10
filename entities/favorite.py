from datetime import datetime
from entities.extensions import db


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'recipe_id', name='uq_user_favorite'),
    )

    def __repr__(self):
        return f'<Favorite user={self.user_id} recipe={self.recipe_id}>'
