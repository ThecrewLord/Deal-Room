from flask import Blueprint
from app.auth.authorization import business_access_required
from app.controllers.solution_design_controller import SolutionDesignController

solution_design_bp = Blueprint("solution_design", __name__, url_prefix="/api/opportunities")

@solution_design_bp.get("/<int:opportunity_id>/solution-design")
@business_access_required
def get_solution_design(opportunity_id):
    return SolutionDesignController.get(opportunity_id)

@solution_design_bp.patch("/<int:opportunity_id>/solution-design")
@business_access_required
def update_solution_design(opportunity_id):
    return SolutionDesignController.update(opportunity_id)
