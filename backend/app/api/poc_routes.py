from flask import Blueprint, request, jsonify

poc_bp = Blueprint("poc", __name__, url_prefix="/api/poc")

@poc_bp.route("/<int:opportunity_id>", methods=["POST"])
def create_poc(opportunity_id):
    data = request.get_json()
    # TODO: call PocController.create(opportunity_id, data) once controller exists
    return jsonify({"message": "Create POC API Working", "opportunity_id": opportunity_id})

@poc_bp.route("/<int:opportunity_id>", methods=["GET"])
def get_poc(opportunity_id):
    # TODO: call PocController.get(opportunity_id) once controller exists
    return jsonify({"message": "Get POC API Working", "opportunity_id": opportunity_id})