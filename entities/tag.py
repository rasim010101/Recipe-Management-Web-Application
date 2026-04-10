from entities.extensions import db

# Many-to-many junction table between Recipe and Tag
recipe_tags = db.Table(
    'recipe_tags',
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipes.id'), primary_key=True),
    db.Column('tag_id',    db.Integer, db.ForeignKey('tags.id'),    primary_key=True)
)


class Tag(db.Model):
    __tablename__ = 'tags'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'
