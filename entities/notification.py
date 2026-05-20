from datetime import datetime
from entities.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recipe_id    = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=True)
    type         = db.Column(db.String(20), nullable=False)
    message      = db.Column(db.String(255), nullable=False)
    is_read      = db.Column(db.Boolean, default=False, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    recipient = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    sender    = db.relationship('User', foreign_keys=[from_user_id])
    recipe    = db.relationship('Recipe', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.id} type={self.type} to={self.user_id}>'
