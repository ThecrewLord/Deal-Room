from flask import Flask, jsonify

from app.config.config import Config, get_database_uri
from app.middleware.cors import configure_cors
from app.database import db, init_db
from app.database.migrate import init_migrations
from app.auth.jwt import init_jwt

# ================================================================
# API BLUEPRINTS
# ================================================================

from app.api.auth_routes import auth_bp
from app.api.poc_routes import poc_bp
from app.api.stakeholder_routes import stakeholder_bp
from app.api.oem_routes import oem_bp
from app.api.activity_routes import activity_bp
from app.api.opportunity_routes import opportunity_bp
from app.api.dashboard_routes import dashboard_bp, legacy_dashboard_bp
from app.api.account_routes import account_bp
from app.api.notification_routes import notification_bp
from app.api.solution_design_routes import solution_design_bp
from app.api.search_routes import search_bp
from app.api.delivery_routes import delivery_bp
from app.api.pre_sales_performance_routes import (
    pre_sales_performance_bp,
)
from app.api.sales_manager_performance_routes import (
    sales_manager_performance_bp,
)

# ================================================================
# MODELS
#
# Import models here so SQLAlchemy knows about all model classes
# before migrations / create_all() are executed.
# ================================================================

from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.poc.poc import Poc
from app.models.opportunity.solution_design import SolutionDesign
from app.models.account.account import Account
from app.models.account.contact import Contact
from app.models.opportunity.stage_master import StageMaster
from app.models.system.tag import Tag
from app.models.system.notification import Notification

# ================================================================
# SERVICES
# ================================================================

from app.services.oem_service import OEMService


def create_app():
    """
    Application factory.

    Creates and configures the Flask application, initializes
    SQLAlchemy/JWT/migrations, imports the required models, and
    registers all API blueprints.
    """

    app = Flask(__name__)

    # ------------------------------------------------------------
    # Load base Flask configuration.
    # ------------------------------------------------------------

    app.config.from_object(Config)

    # ------------------------------------------------------------
    # Database configuration.
    #
    # Tests set DATABASE_URL immediately before create_app().
    # Therefore the URI must be resolved here rather than relying
    # only on the class-level Config value.
    # ------------------------------------------------------------

    database_uri = get_database_uri()

    if not database_uri:
        raise RuntimeError(
            "DATABASE_URL or SQLALCHEMY_DATABASE_URI must be set."
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

    # ------------------------------------------------------------
    # Application extensions.
    # ------------------------------------------------------------

    configure_cors(app)

    init_jwt(app)

    init_db(app)

    init_migrations(app, db)

    # ------------------------------------------------------------
    # Register API blueprints.
    # ------------------------------------------------------------

    app.register_blueprint(auth_bp)

    app.register_blueprint(poc_bp)

    app.register_blueprint(stakeholder_bp)

    app.register_blueprint(oem_bp)

    app.register_blueprint(activity_bp)

    app.register_blueprint(opportunity_bp)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(legacy_dashboard_bp)

    app.register_blueprint(account_bp)

    app.register_blueprint(notification_bp)

    app.register_blueprint(solution_design_bp)

    app.register_blueprint(search_bp)

    app.register_blueprint(pre_sales_performance_bp)

    app.register_blueprint(
        sales_manager_performance_bp
    )
    app.register_blueprint(delivery_bp)
    # ------------------------------------------------------------
    # Root endpoint.
    # ------------------------------------------------------------

    @app.route("/")
    def root():
        return {
            "status": "success",
            "message": "Collaborating Opportunities Backend Running",
        }

    # ------------------------------------------------------------
    # Health endpoint.
    # ------------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok"
        }), 200

    return app