from flask import Blueprint, jsonify, request
from app.services.auth_service import AuthService
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from app.middleware.admin_required import admin_required

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


@auth_bp.post("/signup")
def signup():

    try:

        result = AuthService.signup(
            request.get_json()
        )

        return jsonify(result), 201

    except ValueError as e:

        return jsonify(
            {
                "message": str(e)
            }
        ), 400


@auth_bp.post("/login")
def login():

    try:

        result = AuthService.login(
            request.get_json()
        )

        return jsonify(result), 200

    except ValueError as e:

        return jsonify(
            {
                "message": str(e)
            }
        ), 401

    except PermissionError as e:

        return jsonify(
            {
                "message": str(e)
            }
        ), 403


@auth_bp.post("/select-role")
@jwt_required(refresh=True)
def select_role():

    data = request.get_json()

    result = AuthService.select_role(
        int(get_jwt_identity()),
        data["role"],
    )

    return jsonify(result), 200


@auth_bp.get("/me")
@jwt_required()
def me():

    return jsonify(
        AuthService.me(
            int(get_jwt_identity())
        )
    )


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():

    claims = get_jwt()

    result = AuthService.refresh(
        int(get_jwt_identity()),
        claims.get("active_role"),
    )

    return jsonify(result)


@auth_bp.post("/logout")
@jwt_required()
def logout():

    data = request.get_json() or {}

    refresh_token = data.get(
        "refresh_token"
    )

    auth_header = request.headers.get(
        "Authorization",
        ""
    )

    access_token = auth_header.replace(
        "Bearer ",
        ""
    )

    return jsonify(
        AuthService.logout(
            access_token,
            refresh_token,
        )
    )


@auth_bp.get("/admin/pending")
@jwt_required()
@admin_required
def pending_users():

    return jsonify(
        AuthService.list_pending()
    )


@auth_bp.get("/admin/users")
@jwt_required()
@admin_required
def users():

    return jsonify(
        AuthService.list_users()
    )


@auth_bp.post("/admin/approve/<int:user_id>")
@jwt_required()
@admin_required
def approve(user_id):

    data = request.get_json()

    return jsonify(
        AuthService.approve(
            user_id,
            data["roles"],
        )
    )

@auth_bp.post("/admin/revoke/<int:user_id>")
@jwt_required()
@admin_required
def revoke(user_id):

    return jsonify(
        AuthService.revoke(
            user_id,
        )
    )

