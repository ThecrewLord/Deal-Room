from app import db
from app.models.auth.user import User
from app.models.auth.user_role import Role
from werkzeug.security import generate_password_hash


def seed_admin():
    admin_email = "admin@dataeko.ai"

    existing = User.query.filter_by(email=admin_email).first()

    if existing:
        print("Admin user already exists.")
        return

    admin_role = Role.query.filter_by(name="Admin").first()

    if not admin_role:
        admin_role = Role(name="Admin")
        db.session.add(admin_role)
        db.session.flush()

    admin = User(
        first_name="System",
        last_name="Administrator",
        email=admin_email,
        password_hash=generate_password_hash("Admin@123"),
        status="APPROVED",
    )

    admin.roles.append(admin_role)

    db.session.add(admin)
    db.session.commit()

    print("Admin user seeded successfully.")

__app__ = ["seed_admin", "Role", "User"]