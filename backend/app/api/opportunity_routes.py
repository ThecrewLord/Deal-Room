from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.opportunity_controller import OpportunityController

opportunity_bp = Blueprint("opportunity", __name__, url_prefix="/api/opportunities")


@opportunity_bp.post("")
@business_access_required
def create_opportunity():
    return OpportunityController.create()


@opportunity_bp.get("")
@business_access_required
def get_opportunities():
    return OpportunityController.get_all()


@opportunity_bp.get("/<int:opportunity_id>")
@business_access_required
def get_opportunity(opportunity_id):
    return OpportunityController.get(opportunity_id)


@opportunity_bp.get("/revenue")
@business_access_required
def get_revenue_report():
    return OpportunityController.revenue_report()


@opportunity_bp.get("/<int:opportunity_id>/value-history")
@business_access_required
def get_opportunity_value_history(opportunity_id):
    return OpportunityController.get_value_history(opportunity_id)


@opportunity_bp.get("/<int:opportunity_id>/stage-history")
@business_access_required
def get_opportunity_stage_history(opportunity_id):
    return OpportunityController.get_stage_history(opportunity_id)


@opportunity_bp.post("/<int:opportunity_id>/value")
@business_access_required
def change_opportunity_value(opportunity_id):
    return OpportunityController.change_value(opportunity_id)


@opportunity_bp.post("/<int:opportunity_id>/submit-lead")
@business_access_required
def submit_lead(opportunity_id):
    return OpportunityController.submit_for_review(opportunity_id)


@opportunity_bp.get("/review-queue")
@business_access_required
def get_review_queue():
    return OpportunityController.pending_review()


@opportunity_bp.get("/pre-sales-assignment-queue")
@business_access_required
def get_pre_sales_assignment_queue():
    return OpportunityController.pending_pre_sales_assignment()


@opportunity_bp.get("/pre-sales-assignment-candidates/<path:role>")
@business_access_required
def get_pre_sales_assignment_candidates(role):
    return OpportunityController.eligible_pre_sales_users(role)


@opportunity_bp.get("/sales-owners")
@business_access_required
def get_sales_owners():
    return OpportunityController.eligible_sales_owners()


@opportunity_bp.post("/<int:opportunity_id>/review")
@business_access_required
def review_opportunity(opportunity_id):
    return OpportunityController.review(opportunity_id)


@opportunity_bp.post("/<int:opportunity_id>/advance-to-rfx")
@business_access_required
def advance_to_rfx(opportunity_id):
    return OpportunityController.advance(opportunity_id, "RFX")


@opportunity_bp.post("/<int:opportunity_id>/advance-to-poc")
@business_access_required
def advance_to_poc(opportunity_id):
    return OpportunityController.advance(opportunity_id, "POC")


@opportunity_bp.post("/<int:opportunity_id>/advance-to-negotiations")
@business_access_required
def advance_to_negotiations(opportunity_id):
    return OpportunityController.advance(opportunity_id, "Negotiations")


@opportunity_bp.post("/<int:opportunity_id>/finalize-pre-sales-assignment")
@business_access_required
def finalize_pre_sales_assignment(opportunity_id):
    return OpportunityController.finalize_pre_sales_assignment(opportunity_id)


@opportunity_bp.get("/<int:opportunity_id>/technical-team")
@business_access_required
def get_technical_team(opportunity_id):
    return OpportunityController.get_technical_team(opportunity_id)


@opportunity_bp.post("/<int:opportunity_id>/request-closed-won")
@business_access_required
def request_closed_won(opportunity_id):
    return OpportunityController.request_closed_won(opportunity_id)


@opportunity_bp.post("/<int:opportunity_id>/approve-closed-won")
@business_access_required
def approve_closed_won(opportunity_id):
    return OpportunityController.resolve_closed_won(opportunity_id, True)


@opportunity_bp.post("/<int:opportunity_id>/reject-closed-won")
@business_access_required
def reject_closed_won(opportunity_id):
    return OpportunityController.resolve_closed_won(opportunity_id, False)


@opportunity_bp.post("/<int:opportunity_id>/close-won")
@business_access_required
def close_won(opportunity_id):
    return OpportunityController.close(opportunity_id, True)


@opportunity_bp.post("/<int:opportunity_id>/close-lost")
@business_access_required
def close_lost(opportunity_id):
    return OpportunityController.close(opportunity_id, False)


@opportunity_bp.post("/<int:opportunity_id>/mark-stalled")
@business_access_required
def mark_stalled(opportunity_id):
    return OpportunityController.set_operational_status(opportunity_id, "Stalled")


@opportunity_bp.post("/<int:opportunity_id>/mark-active")
@business_access_required
def mark_active(opportunity_id):
    return OpportunityController.set_operational_status(opportunity_id, "Active")


# Ordinary field update is intentionally retained only for non-state fields.
# The schema rejects stage/status/outcome and requires optimistic concurrency.
@opportunity_bp.put("/<int:opportunity_id>")
@business_access_required
def update_opportunity(opportunity_id):
    return OpportunityController.update(opportunity_id)


@opportunity_bp.delete("/<int:opportunity_id>")
@business_access_required
def delete_opportunity(opportunity_id):
    return OpportunityController.delete(opportunity_id)
