import os

from flask_cors import CORS


def configure_cors(app):
    """Allow the local Vite frontend on both localhost and 127.0.0.1."""
    configured = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = {origin.strip() for origin in configured.split(",") if origin.strip()}
    # Always support both Vite local hostnames. This prevents a download
    # response from losing CORS headers when the browser is opened via
    # localhost vs 127.0.0.1.
    origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
    origins = list(origins)

    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
    )
