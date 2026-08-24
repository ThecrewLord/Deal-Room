from flask import jsonify

from app.services.notification_service import NotificationService


class NotificationController:
    @staticmethod
    def list(user, active_role, unread_only=False):
        return jsonify([
            notification.to_dict()
            for notification in NotificationService.get_for_user(user, active_role, unread_only)
        ])

    @staticmethod
    def mark_read(notification_id, user, active_role):
        notification = NotificationService.mark_read(notification_id, user, active_role)
        if not notification:
            return jsonify({"message": "Notification not found"}), 404
        return jsonify(notification.to_dict())
