from flask_cors import CORS

def configure_cors(app):
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
    )