from flask import Blueprint, g

from app.auth.authorization import business_access_required
from app.controllers.oem_controller import OEMController

oem_bp = Blueprint("oem", __name__, url_prefix="/api/oem")


@oem_bp.get("/")
@business_access_required
def get_oems():
    return OEMController.get_all(g.auth_user, g.active_role)


@oem_bp.get("/<int:oem_id>")
@business_access_required
def get_oem(oem_id):
    return OEMController.get_by_id(oem_id, g.auth_user, g.active_role)


@oem_bp.post("/")
@business_access_required
def create_oem():
    return OEMController.create(g.auth_user, g.active_role)


@oem_bp.put("/<int:oem_id>")
@business_access_required
def update_oem(oem_id):
    return OEMController.update(oem_id, g.auth_user, g.active_role)


@oem_bp.delete("/<int:oem_id>")
@business_access_required
def delete_oem(oem_id):
    return OEMController.delete(oem_id, g.auth_user, g.active_role)
