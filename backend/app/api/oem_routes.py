from flask import Blueprint

from app.controllers.oem_controller import OEMController

oem_bp = Blueprint(
    "oem",
    __name__,
    url_prefix="/api/oem",
)

oem_bp.route("/", methods=["GET"])(OEMController.get_all)
oem_bp.route("/<int:oem_id>", methods=["GET"])(OEMController.get_by_id)
oem_bp.route("/", methods=["POST"])(OEMController.create)
oem_bp.route("/<int:oem_id>", methods=["PUT"])(OEMController.update)
oem_bp.route("/<int:oem_id>", methods=["DELETE"])(OEMController.delete)