from datetime import timedelta
from datetime import datetime
from flask_jwt_extended import (
    decode_token,
    get_jwt,
)
from app.database import db
from app.models.auth.token_blocklist import TokenBlocklist

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)

from app.constants.auth_constants import (
    ACCESS_TOKEN_EXPIRES_MINUTES,
    REFRESH_TOKEN_EXPIRES_DAYS,
)


def create_access(user, active_role):
    return create_access_token(
        identity=str(user.user_id),
        additional_claims={
            "email": user.email,
            "status": user.status,
            "active_role": active_role,
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRES_MINUTES
        ),
    )


def create_refresh(user, active_role=None):
    return create_refresh_token(
        identity=str(user.user_id),
        additional_claims={
            "active_role": active_role
        } if active_role else {},
        expires_delta=timedelta(
            days=REFRESH_TOKEN_EXPIRES_DAYS
        ),
    )


def revoke_token(encoded_token, token_type):
    payload = decode_token(encoded_token)

    db.session.add(
        TokenBlocklist(
            jti=payload["jti"],
            user_id=int(payload["sub"]),
            token_type=token_type,
            expires_at=datetime.fromtimestamp(
                payload["exp"]
            ),
        )
    )

    db.session.commit()




def revoke_current(access_token, refresh_token):
    for encoded_token, token_type in (
        (access_token, "access"),
        (refresh_token, "refresh"),
    ):
        payload = decode_token(encoded_token)

        db.session.add(
            TokenBlocklist(
                jti=payload["jti"],
                user_id=int(payload["sub"]),
                token_type=token_type,
                expires_at=datetime.fromtimestamp(
                    payload["exp"]
                ),
            )
        )

    db.session.commit()