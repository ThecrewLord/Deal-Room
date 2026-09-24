from app.auth.authorization import AuthorizationDenied
from app.constants.roles import ADMIN, LEADERSHIP, SALES_MANAGER, SALES_EXECUTIVE
from app.repositories.dashboard_repository import DashboardRepository
from app.services.opportunity_value_service import RevenueAttributionService


class DashboardService:
    @staticmethod
    def get_dashboard_summary(user, active_role):
        if active_role == ADMIN:
            raise AuthorizationDenied("Admin has no business dashboard.")

        data = {
            "role": active_role,
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
            "pipeline_by_stage": DashboardRepository.get_pipeline_by_stage(user, active_role),
            "recent_opportunities": DashboardRepository.get_recent_opportunities(user, active_role),
            "upcoming_pocs": DashboardRepository.get_upcoming_pocs(user, active_role),
            "recent_activity": DashboardRepository.get_recent_activity(user, active_role),
            "follow_ups": DashboardRepository.get_follow_up_summary(user, active_role),
            "activities": DashboardRepository.get_activity_summary(user, active_role),
            "operational": DashboardRepository.get_role_operational_summary(user, active_role),
        }

        if active_role in {LEADERSHIP, SALES_MANAGER}:
            data["revenue_intelligence"] = {
                "executives": RevenueAttributionService.team_report(user, active_role),
                "closed_won_revenue": DashboardRepository.get_closed_won_revenue(user, active_role),
            }
            data["opportunities_by_owner"] = DashboardRepository.get_opportunities_by_owner(user, active_role)

        if active_role == LEADERSHIP:
            data["executive"] = {
                "pipeline_by_owner": data["opportunities_by_owner"],
                "conversion_rate": data["conversion_rate"],
                "win_loss_ratio": data["win_loss_ratio"],
            }

        if active_role == SALES_EXECUTIVE:
            data["own_revenue"] = RevenueAttributionService.for_sales_executive(user, active_role)

        return data
