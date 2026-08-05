from datetime import datetime
from app.constants.auth_constants import STATUS_APPROVED
from app.auth.password import hash_password, verify_password
from app.auth.token_service import create_access, create_refresh
from app.constants.auth_constants import (
    ROLE_ADMIN,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REVOKED,
)
from flask_jwt_extended import (
    get_jwt_identity,
)

from app.auth.token_service import (
    revoke_current,
)
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.repositories.auth_repository import AuthRepository


class AuthService:

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
            user.roles.append(
                UserRole(role=ROLE_ADMIN)
            )

            user.approved_at = datetime.utcnow()

        AuthRepository.save(user)

        return {
            "message": "Account created successfully.",
            "status": user.status,
        }


    @staticmethod
    def login(data):

        user = AuthRepository.get_by_email(data["email"])

        if not user:
            raise ValueError("Invalid email or password.")

        if not verify_password(
            data["password"],
            user.password_hash,
        ):
            raise ValueError("Invalid email or password.")

        if user.status == STATUS_PENDING:
            raise PermissionError(
                "Your account is awaiting administrator approval."
            )

        if user.status == STATUS_REVOKED:
            raise PermissionError(
                "Your access has been revoked."
            )

        roles = user.role_names()

        if len(roles) == 0:
            raise PermissionError(
                "No role has been assigned."
            )

        if len(roles) > 1:
            return {
                "requires_role_selection": True,
                "roles": roles,
            }

        access = create_access(
            user,
            roles[0],
        )

        refresh = create_refresh(
            user,
            roles[0],
        )

        user.last_login = datetime.utcnow()

        AuthRepository.commit()

        return {
            "access_token": access,
            "refresh_token": refresh,
            "user": user.to_dict(),
        }

    
    @staticmethod
    def select_role(user_id, role):

        user = AuthRepository.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        roles = user.role_names()

        if role not in roles:
            raise PermissionError("Invalid role.")

        return {
            "access_token": create_access(
                user,
                role,
            ),

            "refresh_token": create_refresh(
                user,
                role,
            ),
            
            "user": user.to_dict(),
        }


    @staticmethod
    def me(user_id):

        user = AuthRepository.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        return user.to_dict()


    @staticmethod
    def refresh(user_id, active_role):

        user = AuthRepository.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        return {
            "access_token": create_access(
                user,
                active_role,
            )
        }


    @staticmethod
    def logout(jwt_payload):
        revoke_current(jwt_payload)

        return {
            "message": "Logged out successfully."
        }


    @staticmethod
    def list_pending():

        return [
            user.to_dict()
            for user in AuthRepository.pending_users()
        ]


    @staticmethod
    def list_users():

        return [
            user.to_dict()
            for user in AuthRepository.all_users()
        ]


    @staticmethod
    def approve(user_id, roles):

        user = AuthRepository.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        AuthRepository.delete_roles(user)

        for role in roles:
            AuthRepository.add_role(
                user,
                role,
            )

        user.status = STATUS_APPROVED

        AuthRepository.commit()

        return {
            "message": "User approved successfully."
        }


    @staticmethod
    def revoke(user_id):

        user = AuthRepository.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        user.status = STATUS_REVOKED

        AuthRepository.commit()

        return {
            "message": "User revoked successfully."
        }

    