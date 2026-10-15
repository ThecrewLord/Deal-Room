from flask import Blueprint, g, jsonify
from app.auth.authorization import business_access_required, AuthorizationDenied
from app.services.delivery_performance_service import DeliveryPerformanceService


delivery_performance_bp = Blueprint("delivery_performance", __name__, url_prefix="/api/delivery-manager/team-performance")


def _response(call, error_message):
    try:
        return jsonify(call()), 200
    except AuthorizationDenied as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception:
        return jsonify({"message": error_message}), 500


@delivery_performance_bp.get("")
@business_access_required
def team_performance():
    return _response(lambda: DeliveryPerformanceService.get_team_performance(g.auth_user, g.active_role), "Failed to load delivery team performance.")


@delivery_performance_bp.get("/<int:employee_id>")
@business_access_required
def employee_performance(employee_id):
    try:
        result = DeliveryPerformanceService.get_employee_performance(g.auth_user, g.active_role, employee_id)
        if result is None:
            return jsonify({"message": "Employee not found in your delivery team."}), 404
        return jsonify(result), 200
    except AuthorizationDenied as exc:
        return jsonify({"message": str(exc)}), 403
    except Exception:
        return jsonify({"message": "Failed to load individual delivery performance."}), 500
