from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:

    @staticmethod
    def get_dashboard_summary():

        return {
            "total_opportunities": (
                DashboardRepository.get_total_opportunities()
            ),

            "total_pipeline_value": (
                DashboardRepository.get_total_pipeline_value()
            ),

            "weighted_forecast": (
                DashboardRepository.get_weighted_forecast()
            ),

            "open_opportunities": (
                DashboardRepository.get_open_opportunities()
            ),

            "closed_won": (
                DashboardRepository.get_closed_won()
            ),

            "closed_lost": (
                DashboardRepository.get_closed_lost()
            ),

            "active_pocs": (
                DashboardRepository.get_active_pocs()
            ),
        }