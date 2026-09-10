from flask import Blueprint, jsonify

from app.auth.authorization import business_access_required
from app.controllers.dashboard_controller import DashboardController


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/dashboard",
)


@dashboard_bp.get("")
@business_access_required
def get_dashboard():
    return DashboardController.get_dashboard()


@dashboard_bp.get("/metrics")
@business_access_required
def get_dashboard_metrics():
    return DashboardController.get_dashboard()


legacy_dashboard_bp = Blueprint(
    "legacy_dashboard",
    __name__,
    url_prefix="/dashboard",
)


@legacy_dashboard_bp.get("/metrics")
def legacy_dashboard_metrics():
    # Legacy compatibility endpoint.
    # The current authenticated dashboard remains /api/dashboard.
    return jsonify({
        "message": "Dashboard metrics endpoint",
    }), 200
