from app.auth.authorization import AuthorizationDenied
from app.constants.auth_constants import STATUS_APPROVED
from app.constants.roles import DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.repositories.delivery_performance_repository import DeliveryPerformanceRepository


class DeliveryPerformanceService:
    @staticmethod
    def _require_manager(user, active_role):
        if not (user and user.active and user.status == STATUS_APPROVED and active_role == DELIVERY_MANAGER):
            raise AuthorizationDenied("Only an approved Delivery Manager can view delivery team performance.")

    @staticmethod
    def _employee_payload(employee):
        roles = employee.role_names()
        role = DEVOPS_ENGINEER if DEVOPS_ENGINEER in roles else DATA_ANALYST
        return {"user_id": employee.user_id, "full_name": employee.full_name, "email": employee.email, "role": role, "roles": roles, "manager_id": employee.manager_id}

    @staticmethod
    def get_team_performance(user, active_role):
        DeliveryPerformanceService._require_manager(user, active_role)
        employees = DeliveryPerformanceRepository.get_team_users(user.user_id)
        employee_rows = [{"employee": DeliveryPerformanceService._employee_payload(employee), "metrics": DeliveryPerformanceRepository.get_metrics(employee.user_id)} for employee in employees]
        all_opportunity_ids = set()
        for employee in employees:
            all_opportunity_ids.update(row[0] for row in DeliveryPerformanceRepository._member_query(employee.user_id).with_entities(Opportunity.opportunity_id).distinct().all())
        total_active = sum(item["metrics"]["active_delivery_work"] for item in employee_rows)
        completed = sum(item["metrics"]["completed_work"] for item in employee_rows)
        return {
            "manager": {"user_id": user.user_id, "full_name": user.full_name, "email": user.email},
            "summary": {"delivery_team": len(employees), "assigned_opportunities": len(all_opportunity_ids), "active_delivery_work": total_active, "overdue_work": None, "completed_work": completed, "reporting_period": "current_month", "overdue_tracking_available": False},
            "employees": employee_rows,
        }

    @staticmethod
    def get_employee_performance(user, active_role, employee_id):
        DeliveryPerformanceService._require_manager(user, active_role)
        employee = next((item for item in DeliveryPerformanceRepository.get_team_users(user.user_id) if item.user_id == employee_id), None)
        if not employee:
            return None
        return {
            "employee": DeliveryPerformanceService._employee_payload(employee),
            "metrics": DeliveryPerformanceRepository.get_metrics(employee.user_id),
            "pipeline_by_stage": DeliveryPerformanceRepository.get_pipeline_by_stage(employee.user_id),
            "delivery_by_status": DeliveryPerformanceRepository.get_delivery_by_status(employee.user_id),
            "recent_work": DeliveryPerformanceRepository.get_recent_work(employee.user_id),
        }
