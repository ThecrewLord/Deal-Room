from datetime import datetime

from app import create_app
from app.database import db
from app.models.auth.user import User
from app.auth.password import hash_password

app = create_app()

with app.app_context():
    users = [
        ("Sales Manager", "sales.manager@dealroom.local", "Sales Manager"),
        ("Pre-Sales Manager", "presales.manager@dealroom.local", "Pre-Sales Manager"),
        ("Solution Engineer", "solution.engineer@dealroom.local", "Solution Engineer"),
        ("Delivery Manager", "delivery.manager@dealroom.local", "Delivery Manager"),
        ("DevOps Engineer", "devops.engineer@dealroom.local", "DevOps Engineer"),
        ("Data Analyst", "data.analyst@dealroom.local", "Data Analyst"),
    ]

    for full_name, email, role in users:
        user = User.query.filter_by(email=email).first()

        if user is None:
            user = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password("Test@123"),
                active=True,
                status="APPROVED",
                approved_at=datetime.utcnow(),
                auth_version=1,
            )
            db.session.add(user)
            db.session.flush()

            db.session.execute(
                db.text("""
                    INSERT INTO user_roles (user_id, role)
                    VALUES (:user_id, :role)
                """),
                {
                    "user_id": user.user_id,
                    "role": role,
                },
            )

    db.session.commit()

    print([
        (u.user_id, u.full_name, u.email, u.status, u.active,
         [r.role for r in u.roles])
        for u in User.query.order_by(User.user_id).all()
    ])
