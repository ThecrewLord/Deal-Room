from flask import g, jsonify

from app.constants.roles import SALES_MANAGER
from app.services.sales_manager_performance_service import SalesManagerPerformanceService


class SalesManagerPerformanceController:
    @staticmethod
    def team_performance():
        if g.active_role != SALES_MANAGER:
            return jsonify({"message": "Sales Manager access is required."}), 403

        try:
            return jsonify(
                SalesManagerPerformanceService.team_performance(g.auth_user)
            ), 200
        except Exception:
            return jsonify({"message": "Failed to load Sales Manager team performance."}), 500

    @staticmethod
    def employee_performance(employee_id):
        if g.active_role != SALES_MANAGER:
            return jsonify({"message": "Sales Manager access is required."}), 403

        try:
            data = SalesManagerPerformanceService.employee_performance(
                g.auth_user, employee_id
            )
            if data is None:
                return jsonify({"message": "Employee is not a direct Sales Executive report."}), 404
            return jsonify(data), 200
        except Exception:
            return jsonify({"message": "Failed to load employee performance."}), 500
