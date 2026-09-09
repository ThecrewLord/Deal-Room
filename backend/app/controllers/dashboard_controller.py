from flask import current_app, g, jsonify

from app.services.dashboard_service import DashboardService
from app.constants.roles import ADMIN


class DashboardController:
    @staticmethod
    def get_dashboard():
        try:
            if g.active_role == ADMIN:
                return jsonify({"message": "Admin business dashboard access is not permitted."}), 403
            data = DashboardService.get_dashboard_summary(g.auth_user, g.active_role)
            return jsonify(data), 200
        except Exception:
            current_app.logger.exception("Dashboard load failed for active_role=%s", getattr(g, "active_role", None))
            return jsonify({"message": "Failed to load dashboard"}), 500
