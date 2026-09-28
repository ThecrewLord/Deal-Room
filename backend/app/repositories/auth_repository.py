from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.auth.user_system_permission import UserSystemPermission
from app.constants.auth_constants import STATUS_PENDING, STATUS_APPROVED


class AuthRepository:
    @staticmethod
    def get_by_email(email):
        return User.query.filter(db.func.lower(User.email) == email.lower()).first()

    @staticmethod
    def get_by_id(user_id, for_update=False):
        query = User.query.filter_by(user_id=user_id)
        if for_update:
            query = query.with_for_update()
        return query.first()

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
        return User.query.filter_by(status=STATUS_PENDING).order_by(User.created_at.desc()).all()

    @staticmethod
    def all_users():
        return User.query.order_by(User.created_at.desc()).all()

    @staticmethod
    def system_users_for_admin():
        # Privileged identities are intentionally excluded from delegated Admin
        # visibility.  Leadership gets the unfiltered list.
        return User.query.filter(
            ~User.roles.any(UserRole.role.in_(["Leadership", "Admin"]))
        ).order_by(User.created_at.desc()).all()

    @staticmethod
    def direct_reports(user_id):
        return User.query.filter(User.manager_id == user_id).order_by(User.full_name.asc()).all()

    @staticmethod
    def manager_candidates(required_roles, exclude_user_id=None):
        query = User.query.filter(User.status == STATUS_APPROVED, User.active.is_(True))
        if exclude_user_id is not None:
            query = query.filter(User.user_id != exclude_user_id)
        for role in sorted(required_roles):
            query = query.filter(User.roles.any(UserRole.role == role))
        return query.order_by(User.full_name.asc()).all()

    @staticmethod
    def delete_roles(user):
        UserRole.query.filter_by(user_id=user.user_id).delete(synchronize_session="fetch")

    @staticmethod
    def add_role(user, role):
        user.roles.append(UserRole(role=role))

    @staticmethod
    def replace_roles(user, roles):
        AuthRepository.delete_roles(user)
        for role in roles:
            AuthRepository.add_role(user, role)

    @staticmethod
    def has_system_permission(user_id, permission):
        return UserSystemPermission.query.filter_by(user_id=user_id, permission=permission).first() is not None

    @staticmethod
    def grant_system_permission(user_id, permission):
        existing = UserSystemPermission.query.filter_by(user_id=user_id, permission=permission).first()
        if not existing:
            db.session.add(UserSystemPermission(user_id=user_id, permission=permission))

    @staticmethod
    def revoke_system_permission(user_id, permission):
        UserSystemPermission.query.filter_by(user_id=user_id, permission=permission).delete(synchronize_session="fetch")
