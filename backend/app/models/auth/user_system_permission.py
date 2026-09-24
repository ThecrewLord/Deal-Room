from app.database import db


class UserSystemPermission(db.Model):
    """Explicit delegated system capability for an Admin.

    Roles identify the user's authority domain; this table represents a
    delegated capability that Leadership may grant to an Admin without
    introducing an ``is_admin``/``is_leadership`` flag.
    """

    __tablename__ = "user_system_permissions"
    __table_args__ = (
        db.UniqueConstraint("user_id", "permission", name="uq_user_system_permission"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    permission = db.Column(db.String(100), nullable=False, index=True)
