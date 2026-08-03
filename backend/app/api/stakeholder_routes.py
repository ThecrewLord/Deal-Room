from flask import Blueprint
from app.controllers.stakeholder_controller import StakeholderController

stakeholder_bp = Blueprint("stakeholder", __name__, url_prefix="/api/stakeholder")

stakeholder_bp.route("", methods=["POST"])(StakeholderController.create)
stakeholder_bp.route("/<int:stakeholder_id>", methods=["GET"])(StakeholderController.get)
stakeholder_bp.route("/opportunity/<int:opportunity_id>", methods=["GET"])(StakeholderController.get_by_opportunity)
stakeholder_bp.route("/<int:stakeholder_id>", methods=["PUT"])(StakeholderController.update)
stakeholder_bp.route("/<int:stakeholder_id>", methods=["DELETE"])(StakeholderController.delete)
