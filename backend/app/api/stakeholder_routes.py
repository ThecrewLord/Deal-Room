from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.stakeholder_controller import StakeholderController


stakeholder_bp = Blueprint(
    "stakeholder",
    __name__,
    url_prefix="/api/stakeholder",
)


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
    return StakeholderController.get_by_opportunity(
        opportunity_id
    )


@stakeholder_bp.put("/<int:stakeholder_id>")
@business_access_required
def update_stakeholder(stakeholder_id):
    return StakeholderController.update(stakeholder_id)


@stakeholder_bp.delete("/<int:stakeholder_id>")
@business_access_required
def delete_stakeholder(stakeholder_id):
    return StakeholderController.delete(stakeholder_id)


# ---------------------------------------------------------
# B2 — STAKEHOLDER TAGS
# ---------------------------------------------------------

@stakeholder_bp.post("/<int:stakeholder_id>/tags")
@business_access_required
def add_stakeholder_tag(stakeholder_id):
    return StakeholderController.add_tag(
        stakeholder_id
    )


@stakeholder_bp.get("/<int:stakeholder_id>/tags")
@business_access_required
def get_stakeholder_tags(stakeholder_id):
    return StakeholderController.get_tags(
        stakeholder_id
    )


@stakeholder_bp.delete("/tags/<int:stakeholder_tag_id>")
@business_access_required
def remove_stakeholder_tag(stakeholder_tag_id):
    return StakeholderController.remove_tag(
        stakeholder_tag_id
    )


@stakeholder_bp.get(
    "/opportunity/<int:opportunity_id>/decision-maker"
)
@business_access_required
def get_decision_maker(opportunity_id):
    return StakeholderController.get_decision_maker(
        opportunity_id
    )
