from datetime import datetime, timezone
from threading import RLock

from flask_jwt_extended import get_jwt
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.auth.authorization import AuthorizationService
from app.auth.password import hash_password, verify_password
from app.auth.token_service import create_access, create_refresh, revoke_current
from app.constants.auth_constants import STATUS_APPROVED, STATUS_PENDING, STATUS_REVOKED
from app.constants.roles import (
    ADMIN,
    LEADERSHIP,
    is_valid_role,
)
from app.constants.system_permissions import MANAGE_ADMINS
from app.constants.activity_types import (
    USER_APPROVED,
    USER_ROLE_ADDED,
    USER_ROLE_REMOVED,
    USER_MANAGER_CHANGED,
    USER_ACCESS_REVOKED,
    USER_ADMIN_DELEGATED,
    USER_ADMIN_DELEGATION_REVOKED,
    USER_LEADERSHIP_ASSIGNMENT_ATTEMPTED,
    USER_LEADERSHIP_REMOVAL_BLOCKED,
    USER_LEADERSHIP_ASSIGNED,
)
from app.constants.organizations import get_required_manager_roles
from app.services.activity_service import ActivityService
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.repositories.auth_repository import AuthRepository
from app.database import db


_UNSET = object()
_SECURITY_LOCK_KEY = 918273645
_PROCESS_SECURITY_LOCK = RLock()


class AuthService:
    @staticmethod
    def _security_lock():
        """Serialize root/security mutations in PostgreSQL.

        The advisory lock is transaction-scoped, so the leadership count and
        the role/access mutation share one database-wide serialization boundary.
        PostgreSQL is the production concurrency guarantee; local SQLite tests
        do not pretend to reproduce PostgreSQL locking semantics.
        """
        with _PROCESS_SECURITY_LOCK:
            if db.engine.dialect.name == "postgresql":
                db.session.execute(
                    text("SELECT pg_advisory_xact_lock(:key)"),
                    {"key": _SECURITY_LOCK_KEY},
                )

    @staticmethod
    def _actor(actor_id, active_role=None):
        actor = AuthRepository.get_by_id(actor_id)
        if not actor or not actor.active or actor.status != STATUS_APPROVED:
            raise PermissionError("System administration access required.")
        if active_role is None:
            # Service calls made outside an HTTP request are accepted only for
            # a single system role. In a request, derive the active role from
            # the same central JWT context used by the route. Never union
            # Leadership + Admin merely because both roles are stored.
            try:
                context_user, context_role = AuthorizationService.current_context()
                if context_user.user_id != actor.user_id:
                    raise PermissionError("Authenticated actor mismatch.")
                active_role = context_role
            except RuntimeError:
                system_roles = [role for role in (LEADERSHIP, ADMIN) if actor.has_role(role)]
                if len(system_roles) != 1:
                    raise PermissionError("An explicit active system role is required.")
                active_role = system_roles[0]
        if active_role == LEADERSHIP and actor.has_role(LEADERSHIP):
            return actor, LEADERSHIP
        if active_role == ADMIN and actor.has_role(ADMIN):
            return actor, ADMIN
        raise PermissionError("System administration access required.")

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
    def _is_last_active_leadership(user):
        if not user.has_role(LEADERSHIP):
            return False
        return User.query.filter(
            User.user_id != user.user_id,
            User.active.is_(True),
            User.status == STATUS_APPROVED,
            User.roles.any(role=LEADERSHIP),
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
        seen = {user.user_id}
        current = manager
        while current is not None:
            if current.user_id in seen:
                raise ValueError("Manager assignment would create an organizational cycle.")
            seen.add(current.user_id)
            current = AuthRepository.get_by_id(current.manager_id) if current.manager_id is not None else None
        if not allow_pending and user.status != STATUS_APPROVED:
            raise ValueError("Manager assignment is available only for approved users.")
        return manager

    @staticmethod
    def _validate_dependents_for_new_roles(user, new_roles):
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
    def _authorize_target(actor, active_role, target, requested_roles=None):
        if active_role == LEADERSHIP:
            return
        if target.has_role(LEADERSHIP) or target.has_role(ADMIN):
            raise PermissionError("Only Leadership can manage privileged identities.")
        if requested_roles:
            for role in requested_roles:
                if not AuthorizationService.can_assign_role(actor, active_role, target, role):
                    raise PermissionError("You are not authorized to assign the requested role.")
        elif not AuthorizationService.can_manage_target_roles(actor, active_role, target):
            raise PermissionError("You are not authorized to manage this user.")

    @staticmethod
    def signup(data):
        if not data or not data.get("email") or not data.get("full_name") or not data.get("password"):
            raise ValueError("full_name, email and password are required.")
        # The root-user decision must be serialized before checking count.
        AuthService._security_lock()
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
            user.roles.append(UserRole(role=LEADERSHIP))
            user.approved_at = datetime.utcnow()
        db.session.add(user)
        try:
            db.session.flush()
            result = {"message": "Account created successfully.", "status": user.status}
            db.session.commit()
            return result
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Email already exists.")

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
            return {"requires_role_selection": True, "roles": roles, "refresh_token": refresh, "user": user.to_dict()}
        access = create_access(user, roles[0])
        refresh = create_refresh(user, roles[0])
        AuthRepository.commit()
        return {"access_token": access, "refresh_token": refresh, "active_role": roles[0], "user": user.to_dict()}

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
        return {"access_token": create_access(user, role), "refresh_token": create_refresh(user, role), "active_role": role, "user": user.to_dict()}

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
        if not active_role or not is_valid_role(active_role) or active_role not in user.role_names():
            raise PermissionError("Active role is no longer assigned to this user.")
        return {"access_token": create_access(user, active_role), "active_role": active_role}

    @staticmethod
    def logout(access_token, refresh_token=None):
        revoke_current(access_token, refresh_token)
        return {"message": "Logged out successfully."}

    @staticmethod
    def list_pending(actor_id, active_role=None):
        actor, _ = AuthService._actor(actor_id, active_role)
        return [user.to_dict() for user in AuthRepository.pending_users()]

    @staticmethod
    def list_users(actor_id, active_role=None):
        actor, role = AuthService._actor(actor_id, active_role)
        users = AuthRepository.all_users() if role == LEADERSHIP else AuthRepository.system_users_for_admin()
        return [user.to_dict() for user in users]

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
            {"user_id": c.user_id, "full_name": c.full_name, "email": c.email, "roles": c.role_names()}
            for c in AuthRepository.manager_candidates(required_roles, exclude_user_id=user.user_id)
        ]

    @staticmethod
    def approve(user_id, roles, actor_id=None, manager_id=None, active_role=None):
        actor, active_role = AuthService._actor(actor_id, active_role)
        user = AuthRepository.get_by_id(user_id, for_update=True)
        if not user:
            raise ValueError("User not found.")
        if user.status != STATUS_PENDING:
            raise RuntimeError("Only PENDING users can be approved.")
        AuthService._validate_roles(roles)
        AuthService._authorize_target(actor, active_role, user, roles)
        manager_id = AuthService._normalize_manager_id(manager_id)
        AuthService._validate_manager_assignment(user, roles, manager_id, allow_pending=True)
        try:
            AuthRepository.replace_roles(user, roles)
            user.manager_id = manager_id
            user.status = STATUS_APPROVED
            user.active = True
            user.approved_at = datetime.utcnow()
            user.approved_by = actor.user_id
            user.auth_version += 1
            ActivityService.log("user", user.user_id, USER_APPROVED, f"User '{user.full_name}' approved by {actor.full_name}. Roles: {', '.join(roles)}.", user_id=actor.user_id, commit=False)
            db.session.flush()
            result = user.to_dict()
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_roles(actor_id, user_id, roles, expected_updated_at=None, manager_id=_UNSET, active_role=None):
        AuthService._security_lock()
        actor, active_role = AuthService._actor(actor_id, active_role)
        user = AuthRepository.get_by_id(user_id, for_update=True)
        if not user:
            raise ValueError("User not found.")
        AuthService._validate_roles(roles)
        if actor.user_id == user.user_id and active_role == ADMIN:
            raise PermissionError("Admin cannot change its own roles.")
        if actor.user_id == user.user_id and any(role in {ADMIN, LEADERSHIP} and role not in user.role_names() for role in roles):
            raise PermissionError("Users cannot grant themselves Admin or Leadership.")
        AuthService._authorize_target(actor, active_role, user, roles)

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

        removing_leadership = LEADERSHIP in old and LEADERSHIP not in new
        if removing_leadership and AuthService._is_last_active_leadership(user):
            ActivityService.log("user", user.user_id, USER_LEADERSHIP_REMOVAL_BLOCKED, "Attempt to remove the final active Leadership account.", user_id=actor.user_id, commit=False)
            db.session.commit()
            raise PermissionError("At least one active Leadership account must remain.")

        AuthService._validate_dependents_for_new_roles(user, roles)
        manager = AuthService._validate_manager_assignment(user, roles, desired_manager)
        old_manager = user.manager
        manager_changed = user.manager_id != desired_manager
        if old == new and not manager_changed:
            return user.to_dict()
        try:
            AuthRepository.replace_roles(user, roles)
            user.manager_id = desired_manager
            user.auth_version += 1
            for role in sorted(new - old):
                action = USER_LEADERSHIP_ASSIGNED if role == LEADERSHIP else USER_ROLE_ADDED
                ActivityService.log("user", user.user_id, action, f"Role added: {role}", user_id=actor.user_id, commit=False)
            for role in sorted(old - new):
                ActivityService.log("user", user.user_id, USER_ROLE_REMOVED, f"Role removed: {role}", user_id=actor.user_id, commit=False)
            if manager_changed:
                ActivityService.log("user", user.user_id, USER_MANAGER_CHANGED, f"Manager changed from {old_manager.full_name if old_manager else 'None'} to {manager.full_name if manager else 'None'}.", user_id=actor.user_id, commit=False)
            db.session.flush()
            result = user.to_dict()
            result.update({"old_roles": sorted(old), "added_roles": sorted(new - old), "removed_roles": sorted(old - new), "auth_version": user.auth_version})
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_manager(actor_id, user_id, manager_id, expected_updated_at=None, active_role=None):
        AuthService._security_lock()
        actor, active_role = AuthService._actor(actor_id, active_role)
        user = AuthRepository.get_by_id(user_id, for_update=True)
        if not user:
            raise ValueError("User not found.")
        AuthService._authorize_target(actor, active_role, user)
        manager_id = AuthService._normalize_manager_id(manager_id)
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
            user.auth_version += 1
            ActivityService.log("user", user.user_id, USER_MANAGER_CHANGED, f"Manager changed from {old_manager.full_name if old_manager else 'None'} to {manager.full_name if manager else 'None'}.", user_id=actor.user_id, commit=False)
            db.session.flush()
            result = user.to_dict()
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def revoke(user_id, actor_id=None, active_role=None):
        AuthService._security_lock()
        actor, active_role = AuthService._actor(actor_id, active_role)
        user = AuthRepository.get_by_id(user_id, for_update=True)
        if not user:
            raise ValueError("User not found.")
        if not AuthorizationService.can_revoke_user(actor, active_role, user):
            raise PermissionError("You are not authorized to revoke this user.")
        if user.status == STATUS_REVOKED:
            raise ValueError("User access is already revoked.")
        if user.has_role(LEADERSHIP) and AuthService._is_last_active_leadership(user):
            ActivityService.log("user", user.user_id, USER_LEADERSHIP_REMOVAL_BLOCKED, "Attempt to revoke the final active Leadership account.", user_id=actor.user_id, commit=False)
            db.session.commit()
            raise PermissionError("At least one active Leadership account must remain.")
        AuthService._validate_dependents_for_revocation(user)
        try:
            user.status = STATUS_REVOKED
            user.active = False
            user.auth_version += 1
            ActivityService.log("access", user.user_id, USER_ACCESS_REVOKED, "User access revoked.", user_id=actor.user_id, commit=False)
            db.session.commit()
            return user.to_dict()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def set_admin_delegation(actor_id, user_id, enabled, active_role=None):
        AuthService._security_lock()
        actor, active_role = AuthService._actor(actor_id, active_role)
        if active_role != LEADERSHIP:
            raise PermissionError("Only Leadership can delegate Admin privileges.")
        target = AuthRepository.get_by_id(user_id, for_update=True)
        if not target:
            raise ValueError("User not found.")
        if not target.has_role(ADMIN):
            raise ValueError("Admin delegation can only be granted to an Admin role.")
        if target.has_role(LEADERSHIP):
            raise ValueError("Leadership cannot be delegated as an Admin capability.")
        current = AuthRepository.has_system_permission(target.user_id, MANAGE_ADMINS)
        if current == bool(enabled):
            return target.to_dict()
        try:
            if enabled:
                AuthRepository.grant_system_permission(target.user_id, MANAGE_ADMINS)
                action = USER_ADMIN_DELEGATED
                description = "Leadership delegated Admin-management capability."
            else:
                AuthRepository.revoke_system_permission(target.user_id, MANAGE_ADMINS)
                action = USER_ADMIN_DELEGATION_REVOKED
                description = "Leadership revoked Admin-management capability."
            target.auth_version += 1
            ActivityService.log("user", target.user_id, action, description, user_id=actor.user_id, commit=False)
            db.session.flush()
            result = target.to_dict()
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise
