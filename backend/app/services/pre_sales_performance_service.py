from app.auth.authorization import AuthorizationDenied
from app.constants.roles import PRE_SALES_MANAGER, SOLUTION_ENGINEER
from app.repositories.pre_sales_performance_repository import PreSalesPerformanceRepository


class PreSalesPerformanceService:
    @staticmethod
    def _require_manager(user, active_role):
        if active_role != PRE_SALES_MANAGER:
            raise AuthorizationDenied("Only a Pre-Sales Manager can view technical team performance.")

    @staticmethod
    def _employee_payload(employee):
        roles = employee.role_names()
        technical_role = SOLUTION_ENGINEER
        return {
            "user_id": employee.user_id,
            "full_name": employee.full_name,
            "email": employee.email,
            "last_login": employee.last_login,
            "role": technical_role,
            "roles": roles,
        }

    @staticmethod
    def get_team_performance(user, active_role):
        PreSalesPerformanceService._require_manager(user, active_role)
        employees = PreSalesPerformanceRepository.get_direct_reports(user.user_id)
        return {
            "manager": {"user_id": user.user_id, "full_name": user.full_name, "email": user.email},
            "team_size": len(employees),
            "employees": [
                {
                    "employee": PreSalesPerformanceService._employee_payload(employee),
                    "metrics": PreSalesPerformanceRepository.get_metrics(employee.user_id),
                }
                for employee in employees
            ],
        }

    @staticmethod
    def get_employee_performance(user, active_role, employee_id):
        PreSalesPerformanceService._require_manager(user, active_role)
        employees = PreSalesPerformanceRepository.get_direct_reports(user.user_id)
        employee = next((item for item in employees if item.user_id == employee_id), None)
        if not employee:
            return None
        return {
            "employee": PreSalesPerformanceService._employee_payload(employee),
            "metrics": PreSalesPerformanceRepository.get_metrics(employee.user_id),
            "pipeline_by_stage": PreSalesPerformanceRepository.get_pipeline_by_stage(employee.user_id),
            "poc_by_status": PreSalesPerformanceRepository.get_poc_by_status(employee.user_id),
            "recent_work": PreSalesPerformanceRepository.get_recent_work(employee.user_id),
        }
