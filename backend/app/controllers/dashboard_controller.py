from flask import g, jsonify

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
            return jsonify({"message": "Failed to load dashboard"}), 500
