from flask import Blueprint

from app.auth.authorization import business_access_required
from app.controllers.delivery_project_controller import (
    DeliveryProjectController,
)


delivery_bp = Blueprint(
    "delivery",
    __name__,
    url_prefix="/api/delivery",
)


# ================================================================
# DELIVERY PROJECT
# ================================================================



@delivery_bp.get("/candidates")
@business_access_required
def get_delivery_candidates():
    return DeliveryProjectController.get_candidates()

@delivery_bp.get("/pending")
@business_access_required
def get_pending_delivery_assignments():
    return DeliveryProjectController.get_pending_assignments()

@delivery_bp.post("/projects")
@business_access_required
def create_delivery_project():
    return DeliveryProjectController.create_project()


@delivery_bp.patch("/projects/<int:project_id>/status")
@business_access_required
def update_delivery_project_status(project_id):
    return DeliveryProjectController.update_status(project_id)



@delivery_bp.get("/dashboard")
@business_access_required
def get_delivery_dashboard():
    return DeliveryProjectController.get_dashboard()

@delivery_bp.get("/projects/<int:project_id>")
@business_access_required
def get_delivery_project(project_id):
    return DeliveryProjectController.get_project(project_id)


# ================================================================
# DELIVERY TEAM ASSIGNMENTS
# ================================================================

@delivery_bp.post("/projects/<int:project_id>/assign")
@business_access_required
def assign_delivery_member(project_id):
    return DeliveryProjectController.assign_member(project_id)


@delivery_bp.get("/projects/<int:project_id>/assignments")
@business_access_required
def get_delivery_assignments(project_id):
    return DeliveryProjectController.get_assignments(project_id)


@delivery_bp.delete("/projects/<int:project_id>/assign/<int:user_id>")
@business_access_required
def remove_delivery_member(project_id, user_id):
    return DeliveryProjectController.remove_member(project_id, user_id)