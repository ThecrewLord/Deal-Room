from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.sales_manager_performance_controller import (
    SalesManagerPerformanceController,
)

sales_manager_performance_bp = Blueprint(
    "sales_manager_performance",
    __name__,
    url_prefix="/api/sales-manager",
)


@sales_manager_performance_bp.get("/team-performance")
@business_access_required
def get_team_performance():
    return SalesManagerPerformanceController.team_performance()


@sales_manager_performance_bp.get("/team-performance/<int:employee_id>")
@business_access_required
def get_employee_performance(employee_id):
    return SalesManagerPerformanceController.employee_performance(employee_id)
