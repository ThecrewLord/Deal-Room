from flask import Blueprint, g

from app.auth.authorization import phase2_auth_required
from app.controllers.activity_controller import ActivityController

activity_bp = Blueprint("activity", __name__, url_prefix="/api/activity")


@activity_bp.get("/<string:entity_type>/<int:entity_id>")
@phase2_auth_required
def get_activity(entity_type, entity_id):
    return ActivityController.get_history(
        entity_type, entity_id, g.auth_user, g.active_role
    )
