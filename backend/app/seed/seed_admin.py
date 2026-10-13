from datetime import datetime

from werkzeug.security import generate_password_hash

from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.constants.roles import LEADERSHIP


LEADERSHIP_EMAIL = "leadership@dataeko.ai"
LEADERSHIP_NAME = "System Leadership"
LEADERSHIP_PASSWORD = "ChangeMe123!"


def seed_admin():
    """
    Create or repair the canonical development Leadership user.

    This function is intentionally idempotent:
    running it repeatedly reuses the same user and role.
    """

    user = User.query.filter_by(email=LEADERSHIP_EMAIL).first()

    if user is None:
        user = User(
            full_name=LEADERSHIP_NAME,
            email=LEADERSHIP_EMAIL,
            password_hash=generate_password_hash(LEADERSHIP_PASSWORD),
            active=True,
            status="APPROVED",
            approved_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.flush()

    else:
        # Repair only the development seed user's required state.
        user.full_name = LEADERSHIP_NAME
        user.active = True
        user.status = "APPROVED"

        if user.approved_at is None:
            user.approved_at = datetime.utcnow()

    role = UserRole.query.filter_by(
        user_id=user.user_id,
        role=LEADERSHIP,
    ).first()

    if role is None:
        db.session.add(
            UserRole(
                user_id=user.user_id,
                role=LEADERSHIP,
            )
        )

    db.session.commit()

    return user
