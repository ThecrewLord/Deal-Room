from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.constants.auth_constants import STATUS_PENDING, STATUS_APPROVED


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
        ).order_by(User.created_at.desc()).all()

    @staticmethod
    def all_users():
        return User.query.order_by(
            User.created_at.desc()
        ).all()

    @staticmethod
    def direct_reports(user_id):
        return User.query.filter(User.manager_id == user_id).order_by(User.full_name.asc()).all()

    @staticmethod
    def manager_candidates(required_roles, exclude_user_id=None):
        query = User.query.filter(
            User.status == STATUS_APPROVED,
            User.active.is_(True),
        )
        if exclude_user_id is not None:
            query = query.filter(User.user_id != exclude_user_id)
        for role in sorted(required_roles):
            query = query.filter(User.roles.any(UserRole.role == role))
        return query.order_by(User.full_name.asc()).all()

    @staticmethod
    def delete_roles(user):
        UserRole.query.filter_by(
            user_id=user.user_id
        ).delete(synchronize_session="fetch")

    @staticmethod
    def add_role(user, role):
        user.roles.append(
            UserRole(role=role)
        )

    @staticmethod
    def replace_roles(user, roles):
        """Replace the user's complete role set atomically in the session."""
        AuthRepository.delete_roles(user)
        for role in roles:
            AuthRepository.add_role(user, role)
