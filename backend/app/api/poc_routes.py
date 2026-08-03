from flask import Blueprint
from app.controllers.poc_controller import PocController

poc_bp = Blueprint("poc", __name__, url_prefix="/api/poc")

poc_bp.route("", methods=["POST"])(PocController.create)
poc_bp.route("/<int:poc_id>", methods=["GET"])(PocController.get)
poc_bp.route("/opportunity/<int:opportunity_id>", methods=["GET"])(PocController.get_by_opportunity)
poc_bp.route("/<int:poc_id>", methods=["PUT"])(PocController.update)
poc_bp.route("/<int:poc_id>", methods=["DELETE"])(PocController.delete)