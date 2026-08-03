from app.models.system.audit_log import AuditLog
from app.repositories.activity_repository import ActivityRepository


class ActivityService:

    @staticmethod
    def log(
        entity_type,
        entity_id,
        action,
        description,
        user_id=None,
    ):

        activity = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            performed_by=user_id,
        )

        return ActivityRepository.create(activity)

    @staticmethod
    def get_history(entity_type, entity_id):
        return ActivityRepository.get_by_entity(
            entity_type,
            entity_id,
        )