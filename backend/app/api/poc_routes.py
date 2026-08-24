from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.poc_controller import PocController

poc_bp = Blueprint("poc", __name__, url_prefix="/api/poc")

@poc_bp.post("/request")
@business_access_required
def request_poc():
    return PocController.request()

@poc_bp.get("/<int:poc_id>")
@business_access_required
def get_poc(poc_id):
    return PocController.get(poc_id)

@poc_bp.get("/opportunity/<int:opportunity_id>")
@business_access_required
def get_pocs_by_opportunity(opportunity_id):
    return PocController.get_by_opportunity(opportunity_id)

@poc_bp.get("/pending-approvals")
@business_access_required
def pending_approvals():
    return PocController.pending_approval()

@poc_bp.patch("/<int:poc_id>/design")
@business_access_required
def update_poc_design(poc_id):
    return PocController.update_design(poc_id)

@poc_bp.post("/<int:poc_id>/approve")
@business_access_required
def approve_poc(poc_id):
    return PocController.approve(poc_id)

@poc_bp.post("/<int:poc_id>/reject")
@business_access_required
def reject_poc(poc_id):
    return PocController.reject(poc_id)

@poc_bp.post("/<int:poc_id>/start-execution")
@business_access_required
def start_execution(poc_id):
    return PocController.start_execution(poc_id)

@poc_bp.post("/<int:poc_id>/submit-result")
@business_access_required
def submit_result(poc_id):
    return PocController.submit_result(poc_id)

@poc_bp.post("/<int:poc_id>/complete")
@business_access_required
def complete_poc(poc_id):
    return PocController.complete(poc_id)

@poc_bp.delete("/<int:poc_id>")
@business_access_required
def delete_poc(poc_id):
    return PocController.delete(poc_id)

# Deliberately no generic POST /api/poc or PUT /api/poc/<id>.
# All mutations use explicit Phase 6 business actions.
