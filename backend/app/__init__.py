from flask import Flask
from app.config.config import Config
from app.middleware.cors import configure_cors
from app.database import init_db
from app.auth.jwt import init_jwt

from app.api.auth_routes import auth_bp
from app.api.poc_routes import poc_bp
from app.api.stakeholder_routes import stakeholder_bp
from app.api.oem_routes import oem_bp
from app.api.activity_routes import activity_bp
from app.api.opportunity_routes import opportunity_bp

from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.poc.poc import Poc
from app.models.account.account import Account
from app.models.account.contact import Contact
from app.models.opportunity.stage_master import StageMaster
from app.models.system.tag import Tag
from app.services.oem_service import OEMService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    configure_cors(app)
    init_jwt(app)
    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(poc_bp)
    app.register_blueprint(stakeholder_bp)
    app.register_blueprint(oem_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(opportunity_bp)


    @app.route("/")
    def health():
        return {
            "status": "success",
            "message": "Collaborating Opportunities Backend Running"
        }

    return app

__all__ = [
    "User",
    "UserRole",
    "Poc",
    "Account",
    "Contact",
    "StageMaster",
    "Tag"
]