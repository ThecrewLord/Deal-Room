from flask import Blueprint
from app.controllers.stage_controller import StageController

stage_bp = Blueprint("stage", __name__, url_prefix="/api/stages")

stage_bp.route("", methods=["GET"])(StageController.get_all)
stage_bp.route("/<int:stage_id>", methods=["GET"])(StageController.get)
