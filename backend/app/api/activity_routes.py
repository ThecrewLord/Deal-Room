from flask import Blueprint

from app.controllers.activity_controller import ActivityController

activity_bp = Blueprint(
    "activity",
    __name__,
    url_prefix="/api/activity",
)

activity_bp.route(
    "/<string:entity_type>/<int:entity_id>",
    methods=["GET"],
)(
    ActivityController.get_history
)