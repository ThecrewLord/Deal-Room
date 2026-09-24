"""Seed the canonical development Leadership root user.

This bootstrap is idempotent:
- Reuses an existing Leadership user when one already exists.
- Does not create duplicate Leadership identities.
- Preserves existing authentication data.
- Ensures the canonical development identity has the Leadership role.
"""

from datetime import datetime

from app.auth.password import hash_password
from app.constants.auth_constants import STATUS_APPROVED
from app.constants.roles import LEADERSHIP
from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole


CANONICAL_LEADERSHIP_EMAIL = "leadership@dataeko.ai"
CANONICAL_LEADERSHIP_NAME = "System Leadership"
CANONICAL_LEADERSHIP_PASSWORD = "ChangeMe123!"


def seed_admin():
    """Ensure a Leadership bootstrap account exists without creating duplicates."""

    # 1. Prefer the canonical development Leadership identity.
    user = (
        db.session.query(User)
        .filter(User.email == CANONICAL_LEADERSHIP_EMAIL)
        .one_or_none()
    )

    # 2. If the canonical identity does not exist, reuse the oldest
    #    existing Leadership user rather than creating another one.
    if user is None:
        leadership_role = (
            db.session.query(UserRole)
            .filter(UserRole.role == LEADERSHIP)
            .order_by(UserRole.user_id.asc())
            .first()
        )

        if leadership_role is not None:
            user = db.session.get(User, leadership_role.user_id)

    # 3. Only create a new Leadership account when none exists.
    if user is None:
        user = User(
            full_name=CANONICAL_LEADERSHIP_NAME,
            email=CANONICAL_LEADERSHIP_EMAIL,
            password_hash=hash_password(CANONICAL_LEADERSHIP_PASSWORD),
            active=True,
            status=STATUS_APPROVED,
            approved_at=datetime.utcnow(),
            auth_version=1,
        )

        db.session.add(user)
        db.session.flush()

        db.session.add(
            UserRole(
                user_id=user.user_id,
                role=LEADERSHIP,
            )
        )

    else:
        # 4. Ensure the selected account has the Leadership role.
        existing_role = (
            db.session.query(UserRole)
            .filter(
                UserRole.user_id == user.user_id,
                UserRole.role == LEADERSHIP,
            )
            .one_or_none()
        )

        if existing_role is None:
            db.session.add(
                UserRole(
                    user_id=user.user_id,
                    role=LEADERSHIP,
                )
            )

    db.session.commit()

    print("Leadership root user seeded successfully.")
    return user