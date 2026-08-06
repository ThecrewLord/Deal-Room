from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)


def hash_password(password: str) -> str:
    return generate_password_hash(
        password,
        # method="scrypt",  # doesn't work for this verson of python
        method="pbkdf2:sha256",
    )


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(
        password_hash,
        password,
    )
