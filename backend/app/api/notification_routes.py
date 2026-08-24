from flask import Blueprint, g, request

from app.auth.authorization import phase2_auth_required
from app.controllers.notification_controller import NotificationController

notification_bp = Blueprint("notification", __name__, url_prefix="/api/notifications")


@notification_bp.get("")
@phase2_auth_required
def get_notifications():
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    return NotificationController.list(g.auth_user, g.active_role, unread_only)


@notification_bp.post("/<int:notification_id>/read")
@phase2_auth_required
def mark_notification_read(notification_id):
    return NotificationController.mark_read(notification_id, g.auth_user, g.active_role)
