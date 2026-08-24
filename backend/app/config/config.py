import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Environment-driven configuration for local and deployed environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "deal-room-local-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "deal-room-local-jwt-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=20)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_BLACKLIST_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_PATH = os.getenv("UPLOAD_PATH", "uploads")
    STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "local")
