from datetime import date

from flask import current_app, g, jsonify, request

from app.services.dashboard_service import DashboardService
from app.repositories.dashboard_repository import DashboardRepository
from app.constants.roles import ADMIN


class DashboardController:
    @staticmethod
    def _requested_today():
        raw = request.args.get("today")
        if raw:
            try:
                return date.fromisoformat(raw)
            except (TypeError, ValueError):
                pass
        return date.today()

    @staticmethod
    def get_dashboard():
        try:
            if g.active_role == ADMIN:
                return jsonify({"message": "Admin business dashboard access is not permitted."}), 403
            today = DashboardController._requested_today()
            data = DashboardService.get_dashboard_summary(g.auth_user, g.active_role, today=today)
            return jsonify(data), 200
        except Exception:
            current_app.logger.exception("Dashboard load failed for active_role=%s", getattr(g, "active_role", None))
            return jsonify({"message": "Failed to load dashboard"}), 500

    @staticmethod
    def get_follow_ups():
        try:
            if g.active_role == ADMIN:
                return jsonify({"message": "Admin business dashboard access is not permitted."}), 403
            data = DashboardRepository.get_follow_ups_page(
                g.auth_user,
                g.active_role,
                filter_name=request.args.get("filter", "all"),
                page=request.args.get("page", 1),
                page_size=request.args.get("page_size", 10),
                today=DashboardController._requested_today(),
            )
            return jsonify(data), 200
        except Exception:
            current_app.logger.exception(
                "Dashboard follow-ups load failed for active_role=%s",
                getattr(g, "active_role", None),
            )
            return jsonify({"message": "Failed to load follow-ups"}), 500
