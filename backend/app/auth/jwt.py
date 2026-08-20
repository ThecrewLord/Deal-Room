from flask_jwt_extended import JWTManager

from app.models.auth.token_blocklist import TokenBlocklist

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


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return (
        {
            "message": "Token has expired."
        },
        401,
    )


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return (
        {
            "message": "Invalid token."
        },
        401,
    )


@jwt.unauthorized_loader
def missing_token_callback(error):
    return (
        {
            "message": "Authorization token required."
        },
        401,
    )


@jwt.revoked_token_loader
def revoked(jwt_header, jwt_payload):

    return (
        {
            "message": "Token revoked."
        },
        401,
    )