from datetime import datetime, timezone

from flask_jwt_extended import get_jwt

from app.auth.password import hash_password, verify_password
from app.auth.token_service import create_access, create_refresh, revoke_current
from app.constants.auth_constants import (
    ROLE_ADMIN,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REVOKED,
)
from app.constants.roles import is_valid_role
from app.constants.activity_types import (
    USER_APPROVED,
    USER_ROLE_ADDED,
    USER_ROLE_REMOVED,
    USER_MANAGER_CHANGED,
    USER_ACCESS_REVOKED,
)
from app.constants.organizations import (
    get_organization_for_roles,
    get_required_manager_roles,
)
from app.services.activity_service import ActivityService
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.repositories.auth_repository import AuthRepository
from app.database import db


_UNSET = object()


class AuthService:
    @staticmethod
    def _get_active_admin(actor_id):
        actor = AuthRepository.get_by_id(actor_id)
        if not actor or not actor.active or actor.status != STATUS_APPROVED or not actor.has_role(ROLE_ADMIN):
            raise PermissionError("Admin access required.")
        return actor

    @staticmethod
    def _normalize_timestamp(value):
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @staticmethod
    def _is_last_active_admin(user):
        if not user.has_role(ROLE_ADMIN):
            return False
        return User.query.filter(
            User.user_id != user.user_id,
            User.active.is_(True),
            User.status == STATUS_APPROVED,
            User.roles.any(role=ROLE_ADMIN),
        ).count() == 0

    @staticmethod
    def _validate_roles(roles):
        if not isinstance(roles, list) or not roles:
            raise ValueError("At least one role must be assigned.")
        if len(set(roles)) != len(roles) or any(not is_valid_role(role) for role in roles):
            raise ValueError("Invalid or duplicate role(s).")

    @staticmethod
    def _normalize_manager_id(manager_id):
        if manager_id in (None, ""):
            return None
        try:
            return int(manager_id)
        except (TypeError, ValueError):
            raise ValueError("manager_id must be a valid user ID or null.")

    @staticmethod
    def _validate_manager_assignment(user, roles, manager_id, allow_pending=False):
        manager_id = AuthService._normalize_manager_id(manager_id)
        required_roles = get_required_manager_roles(roles)
        if manager_id is None:
            if required_roles:
                names = ", ".join(sorted(required_roles))
                raise ValueError(f"A valid manager with role(s) {names} is required for the selected roles.")
            return None

        if user.user_id == manager_id:
            raise ValueError("A user cannot be their own manager.")

        manager = AuthRepository.get_by_id(manager_id)
        if not manager:
            raise ValueError("Selected manager was not found.")
        if manager.status != STATUS_APPROVED or not manager.active:
            raise ValueError("Selected manager must be approved and active.")
        if not required_roles:
            raise ValueError("The selected roles do not permit a manager. Use No Manager.")
        missing = required_roles.difference(manager.role_names())
        if missing:
            raise ValueError(
                "Selected manager is not eligible for the user's organization. "
                f"Required role(s): {', '.join(sorted(required_roles))}."
            )

        # Prevent A -> B -> ... -> A cycles before commit.
        seen = {user.user_id}
        current = manager
        while current is not None:
            if current.user_id in seen:
                raise ValueError("Manager assignment would create an organizational cycle.")
            seen.add(current.user_id)
            if current.manager_id is None:
                break
            current = AuthRepository.get_by_id(current.manager_id)

        if not allow_pending and user.status != STATUS_APPROVED:
            raise ValueError("Manager assignment is available only for approved users.")
        return manager

    @staticmethod
    def _validate_dependents_for_new_roles(user, new_roles):
        """Do not leave active employees pointing at an ineligible manager."""
        new_role_set = set(new_roles)
        affected = AuthRepository.direct_reports(user.user_id)
        invalid = []
        for report in affected:
            required = get_required_manager_roles(report.role_names())
            if required and not required.issubset(new_role_set):
                invalid.append(report.full_name)
        if invalid:
            raise ValueError(
                "Role change would invalidate manager relationships for: "
                + ", ".join(invalid)
                + ". Resolve their manager relationships first."
            )

    @staticmethod
    def _validate_dependents_for_revocation(user):
        affected = AuthRepository.direct_reports(user.user_id)
        if affected:
            names = ", ".join(report.full_name for report in affected)
            raise ValueError(
                "This user is currently a manager for: "
                + names
                + ". Resolve those manager relationships before revoking access."
            )

    @staticmethod
    def signup(data):
        existing = AuthRepository.get_by_email(data["email"])
        if existing:
            raise ValueError("Email already exists.")

        first_user = AuthRepository.total_users() == 0
        user = User(
            full_name=data["full_name"],
            email=data["email"],
            password_hash=hash_password(data["password"]),
            status=STATUS_APPROVED if first_user else STATUS_PENDING,
            active=True,
        )
        if first_user:
            user.roles.append(UserRole(role=ROLE_ADMIN))
            user.approved_at = datetime.utcnow()
        AuthRepository.save(user)
        return {"message": "Account created successfully.", "status": user.status}

    @staticmethod
    def login(data):
        user = AuthRepository.get_by_email(data["email"])
        if not user or not verify_password(data["password"], user.password_hash):
            raise ValueError("Invalid email or password.")
        if user.status == STATUS_PENDING:
            raise PermissionError("Your account is awaiting administrator approval.")
        if user.status == STATUS_REVOKED or not user.active:
            raise PermissionError("Your access has been revoked.")

        roles = user.role_names()
        if not roles:
            raise PermissionError("No role has been assigned.")

        user.last_login = datetime.utcnow()
        if len(roles) > 1:
            refresh = create_refresh(user)
            AuthRepository.commit()
            return {
                "requires_role_selection": True,
                "roles": roles,
                "refresh_token": refresh,
                "user": user.to_dict(),
            }

        access = create_access(user, roles[0])
        refresh = create_refresh(user, roles[0])
        AuthRepository.commit()
        return {
            "access_token": access,
            "refresh_token": refresh,
            "active_role": roles[0],
            "user": user.to_dict(),
        }

    @staticmethod
    def select_role(user_id, role, token_auth_version=None):
        if not is_valid_role(role):
            raise PermissionError("Invalid role.")
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if user.status == STATUS_REVOKED or not user.active:
            raise PermissionError("Your access has been revoked.")
        if token_auth_version is None or int(token_auth_version) != int(user.auth_version):
            raise PermissionError("Session is stale. Please sign in again.")
        if role not in user.role_names():
            raise PermissionError("Invalid role.")
        return {
            "access_token": create_access(user, role),
            "refresh_token": create_refresh(user, role),
            "active_role": role,
            "user": user.to_dict(),
        }

    @staticmethod
    def me(user_id):
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        response = user.to_dict()
        response["active_role"] = get_jwt().get("active_role")
        return response

    @staticmethod
    def refresh(user_id, active_role, token_auth_version=None):
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if user.status == STATUS_REVOKED or not user.active:
            raise PermissionError("Your access has been revoked.")
        if token_auth_version is None or int(token_auth_version) != int(user.auth_version):
            raise PermissionError("Session is stale. Please sign in again.")
        if not active_role or active_role not in user.role_names():
            raise PermissionError("Active role is no longer assigned to this user.")
        return {"access_token": create_access(user, active_role), "active_role": active_role}

    @staticmethod
    def logout(access_token, refresh_token=None):
        revoke_current(access_token, refresh_token)
        return {"message": "Logged out successfully."}

    @staticmethod
    def list_pending():
        return [user.to_dict() for user in AuthRepository.pending_users()]

    @staticmethod
    def list_users():
        return [user.to_dict() for user in AuthRepository.all_users()]

    @staticmethod
    def manager_candidates(user_id, proposed_roles=None):
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        roles = user.role_names() if proposed_roles is None else proposed_roles
        if not roles:
            return []
        AuthService._validate_roles(roles)
        required_roles = get_required_manager_roles(roles)
        if not required_roles:
            return []
        return [
            {
                "user_id": candidate.user_id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "roles": candidate.role_names(),
            }
            for candidate in AuthRepository.manager_candidates(required_roles, exclude_user_id=user.user_id)
        ]

    @staticmethod
    def approve(user_id, roles, actor_id=None, manager_id=None):
        actor = AuthService._get_active_admin(actor_id)
        manager_id = AuthService._normalize_manager_id(manager_id)
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if user.status != STATUS_PENDING:
            raise RuntimeError("Only PENDING users can be approved.")
        AuthService._validate_roles(roles)
        AuthService._validate_manager_assignment(user, roles, manager_id, allow_pending=True)

        try:
            AuthRepository.replace_roles(user, roles)
            user.manager_id = manager_id
            user.status = STATUS_APPROVED
            user.active = True
            user.approved_at = datetime.utcnow()
            user.approved_by = actor.user_id
            user.auth_version += 1
            manager_text = user.manager.full_name if user.manager else "None"
            ActivityService.log(
                "user", user.user_id, USER_APPROVED,
                f"User '{user.full_name}' approved by {actor.full_name}. Roles: {', '.join(roles)}. Manager: {manager_text}.",
                user_id=actor.user_id, commit=False,
            )
            db.session.flush()
            result = user.to_dict()
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_roles(actor_id, user_id, roles, expected_updated_at=None, manager_id=_UNSET):
        actor = AuthService._get_active_admin(actor_id)
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        AuthService._validate_roles(roles)

        if expected_updated_at is not None:
            expected = AuthService._normalize_timestamp(expected_updated_at)
            actual = AuthService._normalize_timestamp(user.updated_at)
            if expected != actual:
                raise RuntimeError("User was modified by another administrator.")

        old = set(user.role_names())
        new = set(roles)
        desired_manager = user.manager_id if manager_id is _UNSET else AuthService._normalize_manager_id(manager_id)

        if old == new and manager_id is _UNSET:
            return user.to_dict()

        if actor.user_id == user.user_id and ROLE_ADMIN not in new:
            raise PermissionError("You cannot remove your final Admin role.")
        if ROLE_ADMIN in old and ROLE_ADMIN not in new and AuthService._is_last_active_admin(user):
            raise PermissionError("At least one active Admin must remain.")

        AuthService._validate_dependents_for_new_roles(user, roles)
        manager = AuthService._validate_manager_assignment(user, roles, desired_manager)
        old_manager = user.manager
        old_manager_name = old_manager.full_name if old_manager else "None"
        manager_changed = user.manager_id != desired_manager
        if old == new and not manager_changed:
            return user.to_dict()
        try:
            AuthRepository.replace_roles(user, roles)
            user.manager_id = desired_manager
            user.auth_version += 1

            for role in sorted(new - old):
                ActivityService.log(
                    "user", user.user_id, USER_ROLE_ADDED,
                    f"Role added: {role}", user_id=actor.user_id, commit=False,
                )
            for role in sorted(old - new):
                ActivityService.log(
                    "user", user.user_id, USER_ROLE_REMOVED,
                    f"Role removed: {role}", user_id=actor.user_id, commit=False,
                )
            if manager_changed:
                new_manager_name = manager.full_name if manager else "None"
                ActivityService.log(
                    "user", user.user_id, USER_MANAGER_CHANGED,
                    f"Manager changed from {old_manager_name} to {new_manager_name}.",
                    user_id=actor.user_id, commit=False,
                )

            db.session.flush()
            result = user.to_dict()
            result.update({
                "old_roles": sorted(old),
                "added_roles": sorted(new - old),
                "removed_roles": sorted(old - new),
                "auth_version": user.auth_version,
            })
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_manager(actor_id, user_id, manager_id, expected_updated_at=None):
        actor = AuthService._get_active_admin(actor_id)
        manager_id = AuthService._normalize_manager_id(manager_id)
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if user.status != STATUS_APPROVED or not user.active:
            raise ValueError("Only approved active users can have their manager changed.")

        if expected_updated_at is not None:
            expected = AuthService._normalize_timestamp(expected_updated_at)
            actual = AuthService._normalize_timestamp(user.updated_at)
            if expected != actual:
                raise RuntimeError("User was modified by another administrator.")

        if user.manager_id == manager_id:
            return user.to_dict()

        old_manager = user.manager
        manager = AuthService._validate_manager_assignment(user, user.role_names(), manager_id)
        try:
            user.manager_id = manager_id
            ActivityService.log(
                "user", user.user_id, USER_MANAGER_CHANGED,
                f"Manager changed from {old_manager.full_name if old_manager else 'None'} to {manager.full_name if manager else 'None'}.",
                user_id=actor.user_id, commit=False,
            )
            db.session.flush()
            result = user.to_dict()
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def revoke(user_id, actor_id=None):
        actor = AuthService._get_active_admin(actor_id)
        user = AuthRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if actor.user_id == user.user_id:
            raise PermissionError("You cannot revoke your own access.")
        if user.status == STATUS_REVOKED:
            raise ValueError("User access is already revoked.")
        if AuthService._is_last_active_admin(user):
            raise PermissionError("At least one active Admin must remain.")
        AuthService._validate_dependents_for_revocation(user)

        try:
            user.status = STATUS_REVOKED
            user.active = False
            user.auth_version += 1
            ActivityService.log(
                "access", user.user_id, USER_ACCESS_REVOKED,
                "User access revoked.", user_id=actor.user_id, commit=False,
            )
            db.session.commit()
            return user.to_dict()
        except Exception:
            db.session.rollback()
            raise
