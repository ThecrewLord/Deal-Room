import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "change-this-secret",
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=20
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=7
    )
    JWT_TOKEN_LOCATION = [
        "headers",
    ]
    JWT_BLACKLIST_ENABLED = True

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_PATH = os.getenv("UPLOAD_PATH", "uploads")
    STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "local")