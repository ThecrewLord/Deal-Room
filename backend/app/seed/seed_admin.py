"""Idempotent bootstrap for a development Leadership root account."""
from datetime import datetime

from app.auth.password import hash_password
from app.constants.auth_constants import STATUS_APPROVED
from app.constants.roles import LEADERSHIP
from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole


def seed_admin():
    email = "leadership@dataeko.ai"
    existing = User.query.filter_by(email=email).first()
    if existing:
        return existing

    leadership = User(
        full_name="System Leadership",
        email=email,
        password_hash=hash_password("Leadership@123"),
        status=STATUS_APPROVED,
        active=True,
        approved_at=datetime.utcnow(),
    )
    leadership.roles.append(UserRole(role=LEADERSHIP))
    db.session.add(leadership)
    db.session.commit()
    print("Leadership root user seeded successfully.")
    return leadership
