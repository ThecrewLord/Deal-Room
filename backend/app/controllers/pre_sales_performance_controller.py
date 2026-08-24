from flask import g, jsonify

from app.auth.authorization import AuthorizationDenied
from app.services.pre_sales_performance_service import PreSalesPerformanceService


class PreSalesPerformanceController:
    @staticmethod
    def team():
        try:
            return jsonify(PreSalesPerformanceService.get_team_performance(g.auth_user, g.active_role)), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except Exception:
            return jsonify({"message": "Failed to load technical team performance."}), 500

    @staticmethod
    def employee(employee_id):
        try:
            result = PreSalesPerformanceService.get_employee_performance(g.auth_user, g.active_role, employee_id)
            if not result:
                return jsonify({"message": "Employee not found in your technical team."}), 404
            return jsonify(result), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except Exception:
            return jsonify({"message": "Failed to load employee performance."}), 500
