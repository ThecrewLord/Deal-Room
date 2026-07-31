from app.database import db
from app.models.base import BaseModel


class Tag(BaseModel):
    __tablename__ = "tags"

    tag_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    color = db.Column(
        db.String(20),
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self):
        return f"<Tag {self.name}>"