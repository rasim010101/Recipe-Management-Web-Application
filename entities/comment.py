from datetime import datetime
from entities.extensions import db


class Comment(db.Model):
    __tablename__ = 'comments'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),    nullable=False)
    recipe_id  = db.Column(db.Integer, db.ForeignKey('recipes.id'),  nullable=False)
    parent_id  = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    body       = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    replies = db.relationship('Comment',
                              backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic')

    def __repr__(self):
        return f'<Comment {self.id} user={self.user_id}>'
