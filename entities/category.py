from datetime import datetime
from entities.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), unique=True, nullable=False)
    slug        = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    image_path  = db.Column(db.String(512), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    recipes = db.relationship('Recipe', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'
