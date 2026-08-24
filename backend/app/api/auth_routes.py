from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.middleware.admin_required import admin_required
from app.auth.authorization import phase2_auth_required
from app.services.auth_service import AuthService


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/signup")
def signup():
    try:
        result = AuthService.signup(request.get_json())
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.post("/login")
def login():
    try:
        result = AuthService.login(request.get_json())
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 401
    except PermissionError as e:
        return jsonify({"message": str(e)}), 403


@auth_bp.post("/select-role")
@jwt_required(refresh=True)
def select_role():
    data = request.get_json() or {}
    role = data.get("role")
    try:
        result = AuthService.select_role(int(get_jwt_identity()), role, get_jwt().get("auth_version"))
        return jsonify(result), 200
    except RuntimeError as e:
        return jsonify({"message": str(e)}), 409
    except PermissionError as e:
        message = str(e)
        return jsonify({"message": message}), 401 if "stale" in message.lower() else 403
    except ValueError as e:
        return jsonify({"message": str(e)}), 403


@auth_bp.get("/me")
@phase2_auth_required
def me():
    return jsonify(AuthService.me(int(get_jwt_identity())))


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    claims = get_jwt()
    try:
        result = AuthService.refresh(int(get_jwt_identity()), claims.get("active_role"), claims.get("auth_version"))
        return jsonify(result)
    except RuntimeError as e:
        return jsonify({"message": str(e)}), 409
    except PermissionError as e:
        message = str(e)
        return jsonify({"message": message}), 401 if "stale" in message.lower() else 403
    except ValueError as e:
        return jsonify({"message": str(e)}), 403


@auth_bp.post("/logout")
@jwt_required()
def logout():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.replace("Bearer ", "")
    return jsonify(AuthService.logout(access_token, refresh_token))


@auth_bp.get("/admin/pending")
@jwt_required()
@admin_required
def pending_users():
    return jsonify(AuthService.list_pending())


@auth_bp.get("/admin/users")
@jwt_required()
@admin_required
def users():
    return jsonify(AuthService.list_users())


@auth_bp.get("/admin/users/<int:user_id>/manager-candidates")
@jwt_required()
@admin_required
def manager_candidates(user_id):
    raw_roles = request.args.getlist("role")
    roles = raw_roles or None
    try:
        return jsonify(AuthService.manager_candidates(user_id, roles))
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.post("/admin/approve/<int:user_id>")
@jwt_required()
@admin_required
def approve(user_id):
    data = request.get_json() or {}
    try:
        return jsonify(AuthService.approve(user_id, data.get("roles"), int(get_jwt_identity()), data.get("manager_id")))
    except RuntimeError as e:
        return jsonify({"message": str(e)}), 409
    except (ValueError, PermissionError) as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.post("/admin/users/<int:user_id>/roles")
@jwt_required()
@admin_required
def update_roles(user_id):
    data = request.get_json() or {}
    try:
        if "manager_id" in data:
            result = AuthService.update_roles(
                int(get_jwt_identity()), user_id, data.get("roles"), data.get("updated_at"), data.get("manager_id")
            )
        else:
            # Backward-compatible role-only requests preserve the current manager.
            result = AuthService.update_roles(
                int(get_jwt_identity()), user_id, data.get("roles"), data.get("updated_at")
            )
        return jsonify(result), 200
    except RuntimeError as e:
        return jsonify({"message": str(e)}), 409
    except PermissionError as e:
        return jsonify({"message": str(e)}), 403
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.patch("/admin/users/<int:user_id>/manager")
@auth_bp.post("/admin/users/<int:user_id>/manager")
@jwt_required()
@admin_required
def update_manager(user_id):
    data = request.get_json() or {}
    try:
        result = AuthService.update_manager(
            int(get_jwt_identity()), user_id, data.get("manager_id"), data.get("updated_at")
        )
        return jsonify(result), 200
    except RuntimeError as e:
        return jsonify({"message": str(e)}), 409
    except PermissionError as e:
        return jsonify({"message": str(e)}), 403
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.post("/admin/revoke/<int:user_id>")
@jwt_required()
@admin_required
def revoke(user_id):
    try:
        return jsonify(AuthService.revoke(user_id, int(get_jwt_identity())))
    except PermissionError as e:
        return jsonify({"message": str(e)}), 403
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
