from flask import Flask
from app.config.config import Config
from app.middleware.cors import configure_cors
from app.database import db, init_db
from app.database.migrate import init_migrations
from app.auth.jwt import init_jwt

from app.api.auth_routes import auth_bp
from app.api.poc_routes import poc_bp
from app.api.stakeholder_routes import stakeholder_bp
from app.api.oem_routes import oem_bp
from app.api.activity_routes import activity_bp
from app.api.opportunity_routes import opportunity_bp
from app.api.dashboard_routes import dashboard_bp
from app.api.account_routes import account_bp
from app.api.notification_routes import notification_bp
from app.api.solution_design_routes import solution_design_bp
from app.api.search_routes import search_bp
from app.api.pre_sales_performance_routes import pre_sales_performance_bp
from app.api.sales_manager_performance_routes import sales_manager_performance_bp

from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.poc.poc import Poc
from app.models.opportunity.solution_design import SolutionDesign
from app.models.account.account import Account
from app.models.account.contact import Contact
from app.models.opportunity.stage_master import StageMaster
from app.models.system.tag import Tag
from app.models.system.notification import Notification
from app.services.oem_service import OEMService

from flask import jsonify

def create_app():
    
    app = Flask(__name__)
    app.config.from_object(Config)

    configure_cors(app)
    init_jwt(app)
    init_db(app)
    init_migrations(app, db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(poc_bp)
    app.register_blueprint(stakeholder_bp)
    app.register_blueprint(oem_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(opportunity_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(solution_design_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(pre_sales_performance_bp)
    app.register_blueprint(sales_manager_performance_bp)
    
    @app.route("/")
    def root():
        return {
            "status": "success",
            "message": "Collaborating Opportunities Backend Running"
        }

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

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