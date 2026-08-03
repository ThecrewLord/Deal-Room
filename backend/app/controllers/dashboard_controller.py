from flask import jsonify

from app.services.dashboard_service import DashboardService


class DashboardController:

    @staticmethod
    def get_dashboard():

        try:
            data = DashboardService.get_dashboard_summary()

            return (
                jsonify(data),
                200,
            )

        except Exception as e:

            return (
                jsonify(
                    {
                        "message": "Failed to load dashboard",
                        "error": str(e),
                    }
                ),
                500,
            )