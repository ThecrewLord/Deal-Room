from datetime import datetime

from app.database import db


class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    jti = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    token_type = db.Column(
        db.String(20),
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False,
    )

    revoked_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )