from app.auth.authorization import AuthorizationService
from app.models.system.audit_log import AuditLog
from app.repositories.activity_repository import ActivityRepository


class ActivityService:
    @staticmethod
    def log(entity_type, entity_id, action, description, user_id=None, commit=True):
        activity = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            performed_by=user_id,
        )
        if commit:
            return ActivityRepository.create(activity)
        from app.database import db
        db.session.add(activity)
        return activity

    @staticmethod
    def get_history(entity_type, entity_id, user, active_role):
        if not AuthorizationService.can_view_activity(user, active_role, entity_type, entity_id):
            return None
        return ActivityRepository.get_by_entity(entity_type, entity_id)
