from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    @staticmethod
    def get_dashboard_summary(user, active_role):
        return {
            "total_opportunities": DashboardRepository.get_total_opportunities(user, active_role),
            "total_pipeline_value": DashboardRepository.get_total_pipeline_value(user, active_role),
            "weighted_forecast": DashboardRepository.get_weighted_forecast(user, active_role),
            "open_opportunities": DashboardRepository.get_open_opportunities(user, active_role),
            "closed_won": DashboardRepository.get_closed_won(user, active_role),
            "closed_lost": DashboardRepository.get_closed_lost(user, active_role),
            "conversion_rate": DashboardRepository.get_conversion_rate(user, active_role),
            "stage_ageing": DashboardRepository.get_stage_ageing(user, active_role),
            "average_stage_ageing": DashboardRepository.get_average_stage_ageing(user, active_role),
            "stalled_deals": DashboardRepository.get_stalled_deals(user, active_role),
            "active_pocs": DashboardRepository.get_active_pocs(user, active_role),
            "win_loss_ratio": DashboardRepository.get_win_loss_ratio(user, active_role),
            "partner_contribution": DashboardRepository.get_partner_contribution(user, active_role),
            "pipeline_by_stage": DashboardRepository.get_pipeline_by_stage(user, active_role),
            "recent_opportunities": DashboardRepository.get_recent_opportunities(user, active_role),
            "upcoming_pocs": DashboardRepository.get_upcoming_pocs(user, active_role),
            "recent_activity": DashboardRepository.get_recent_activity(user, active_role),
        }
