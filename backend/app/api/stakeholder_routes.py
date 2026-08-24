from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.stakeholder_controller import StakeholderController

stakeholder_bp = Blueprint("stakeholder", __name__, url_prefix="/api/stakeholder")


@stakeholder_bp.post("")
@business_access_required
def create_stakeholder():
    return StakeholderController.create()


@stakeholder_bp.get("/<int:stakeholder_id>")
@business_access_required
def get_stakeholder(stakeholder_id):
    return StakeholderController.get(stakeholder_id)


@stakeholder_bp.get("/opportunity/<int:opportunity_id>")
@business_access_required
def get_stakeholders_by_opportunity(opportunity_id):
    return StakeholderController.get_by_opportunity(opportunity_id)


@stakeholder_bp.put("/<int:stakeholder_id>")
@business_access_required
def update_stakeholder(stakeholder_id):
    return StakeholderController.update(stakeholder_id)


@stakeholder_bp.delete("/<int:stakeholder_id>")
@business_access_required
def delete_stakeholder(stakeholder_id):
    return StakeholderController.delete(stakeholder_id)
