from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.roles import ADMIN


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            user, active_role = AuthorizationService.current_context()
        except AuthorizationDenied as exc:
            message = str(exc)
            status = 401 if "stale" in message.lower() else 403
            return jsonify({"message": message}), status

        if active_role != ADMIN:
            return (
                jsonify({"message": "Admin access required."}),
                403,
            )

        return fn(*args, **kwargs)

    return wrapper
