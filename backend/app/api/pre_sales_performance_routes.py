from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.pre_sales_performance_controller import PreSalesPerformanceController


pre_sales_performance_bp = Blueprint(
    "pre_sales_performance",
    __name__,
    url_prefix="/api/pre-sales-manager/team-performance",
)


@pre_sales_performance_bp.get("")
@business_access_required
def get_team_performance():
    return PreSalesPerformanceController.team()


@pre_sales_performance_bp.get("/<int:employee_id>")
@business_access_required
def get_employee_performance(employee_id):
    return PreSalesPerformanceController.employee(employee_id)
