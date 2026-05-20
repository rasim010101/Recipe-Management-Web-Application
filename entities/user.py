from datetime import datetime
from flask_login import UserMixin
from entities.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(100), unique=True, nullable=False)
    email         = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20), default='user')
    bio           = db.Column(db.Text, nullable=True)
    avatar_path   = db.Column(db.String(512), nullable=True)
    is_active          = db.Column(db.Boolean, default=True,  nullable=False)
    is_email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    email_confirmed_at = db.Column(db.DateTime, nullable=True)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at         = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recipes   = db.relationship('Recipe', backref='author', lazy='dynamic',
                                foreign_keys='Recipe.author_id')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    ratings   = db.relationship('Rating',   backref='user', lazy='dynamic')
    comments  = db.relationship('Comment',  backref='user', lazy='dynamic')

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'
