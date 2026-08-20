from app.database import db


class UserRole(db.Model):
    __tablename__ = "user_roles"

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "role",
            name="uq_user_role",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    role = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    ) 