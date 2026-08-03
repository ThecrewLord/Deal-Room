from flask import jsonify

from app.services.activity_service import ActivityService


class ActivityController:

    @staticmethod
    def get_history(entity_type, entity_id):

        logs = ActivityService.get_history(
            entity_type,
            entity_id,
        )

        return jsonify([
            {
                "audit_log_id": log.audit_log_id,
                "action": log.action,
                "description": log.description,
                "performed_by": log.performed_by,
                "created_at": log.created_at,
            }
            for log in logs
        ])