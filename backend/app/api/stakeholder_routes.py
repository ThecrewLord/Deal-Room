from flask import Blueprint, request, jsonify

stakeholder_bp = Blueprint("stakeholder", __name__, url_prefix="/api/stakeholder")

@stakeholder_bp.route("/<int:opportunity_id>", methods=["POST"])
def create_stakeholder(opportunity_id):
    data = request.get_json()
    # TODO: call StakeholderController.create(opportunity_id, data) once controller exists
    return jsonify({"message": "Create Stakeholder API Working", "opportunity_id": opportunity_id})

@stakeholder_bp.route("/<int:opportunity_id>", methods=["GET"])
def get_stakeholders(opportunity_id):
    # TODO: call StakeholderController.get(opportunity_id) once controller exists
    return jsonify({"message": "Get Stakeholders API Working", "opportunity_id": opportunity_id})