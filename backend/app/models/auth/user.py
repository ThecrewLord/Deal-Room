from datetime import datetime

from app.database import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(
        db.String(150),
        nullable=False,
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    # ----------------------------
    # Authentication
    # ----------------------------

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING",
    )

    last_login = db.Column(
        db.DateTime,
        nullable=True,
    )

    approved_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    approved_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=True,
    )

    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=True,
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    auth_version = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    roles = db.relationship(
        "UserRole",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    manager = db.relationship(
        "User",
        remote_side=[user_id],
        foreign_keys=[manager_id],
        backref=db.backref("direct_reports", lazy=True),
    )

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "email": self.email,
            "status": self.status,
            "active": self.active,
            "roles": [role.role for role in self.roles],
            "manager_id": self.manager_id,
            "manager_name": self.manager.full_name if self.manager else None,
            "organization": self.organization(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def organization(self):
        from app.constants.organizations import get_organization_for_roles
        return get_organization_for_roles(self.role_names())

    def has_role(self, role_name):
        return any(
            role.role == role_name
            for role in self.roles
        )


    def role_names(self):
        return [
            role.role
            for role in self.roles
        ]