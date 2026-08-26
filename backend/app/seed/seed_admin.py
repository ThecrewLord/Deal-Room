from app.auth.password import hash_password
from app.constants.auth_constants import STATUS_APPROVED
from app.constants.roles import ADMIN
from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole


def seed_admin():
    admin_email = "admin@dataeko.ai"
    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        print("Admin user already exists.")
        return existing

    admin = User(
        full_name="System Administrator",
        email=admin_email,
        password_hash=hash_password("Admin@123"),
        status=STATUS_APPROVED,
        active=True,
        approved_at=__import__("datetime").datetime.utcnow(),
    )
    admin.roles.append(UserRole(role=ADMIN))
    db.session.add(admin)
    db.session.commit()
    print("Admin user seeded successfully.")
    return admin
