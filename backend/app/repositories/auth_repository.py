from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.constants.auth_constants import STATUS_PENDING


class AuthRepository:

    @staticmethod
    def get_by_email(email):
        return User.query.filter(
            db.func.lower(User.email) == email.lower()
        ).first()

    @staticmethod
    def get_by_id(user_id):
        return User.query.filter_by(
            user_id=user_id
        ).first()

    @staticmethod
    def total_users():
        return User.query.count()

    @staticmethod
    def save(user):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def pending_users():
        return User.query.filter_by(
            status=STATUS_PENDING
        ).all()

    @staticmethod
    def all_users():
        return User.query.order_by(
            User.created_at.desc()
        ).all()

    @staticmethod
    def delete_roles(user):
        UserRole.query.filter_by(
            user_id=user.user_id
        ).delete()

    @staticmethod
    def add_role(user, role):
        user.roles.append(
            UserRole(
                role=role
            )
        )