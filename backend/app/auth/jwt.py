from flask_jwt_extended import JWTManager
from flask import jsonify

from app.models.auth.token_blocklist import TokenBlocklist
from app.models.auth.user import User
from app.database import db

jwt = JWTManager()


def init_jwt(app):
    jwt.init_app(app)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return (
        TokenBlocklist.query.filter_by(
            jti=jwt_payload["jti"]
        ).first()
        is not None
    )


@jwt.token_verification_failed_loader
def token_verification_failed(jwt_header, jwt_payload):
    return jsonify({"message": "Invalid token."}), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return ({"message": "Token has expired."}, 401)


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return ({"message": "Invalid token."}, 401)


@jwt.unauthorized_loader
def missing_token_callback(error):
    return ({"message": "Authorization token required."}, 401)


@jwt.revoked_token_loader
def revoked(jwt_header, jwt_payload):
    return ({"message": "Token revoked."}, 401)


@jwt.token_verification_loader
def verify_token_version(jwt_header, jwt_payload):
    """
    Reject tokens created before the user's auth_version changed.

    Every access/refresh token contains the auth_version that existed
    when the token was issued.
    """

    user_id = jwt_payload.get("sub")
    token_version = jwt_payload.get("auth_version")

    if user_id is None or token_version is None:
        return False

    try:
        user_id = int(user_id)
        token_version = int(token_version)
    except (TypeError, ValueError):
        return False

    database_version = db.session.execute(
        db.select(User.auth_version).where(
            User.user_id == user_id
        )
    ).scalar_one_or_none()

    if database_version is None:
        return False

    return token_version == int(database_version)
