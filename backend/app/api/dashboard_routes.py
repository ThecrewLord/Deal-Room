from flask import Blueprint

from app.controllers.dashboard_controller import (
    DashboardController,
)

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard",
)

dashboard_bp.route(
    "",
    methods=["GET"],
)(
    DashboardController.get_dashboard
)