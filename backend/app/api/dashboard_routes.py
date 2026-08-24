from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.dashboard_controller import DashboardController

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("")
@business_access_required
def get_dashboard():
    return DashboardController.get_dashboard()
