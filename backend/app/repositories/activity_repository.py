from app.database import db
from app.models.system.audit_log import AuditLog


class ActivityRepository:

    @staticmethod
    def create(activity):
        db.session.add(activity)
        db.session.commit()
        return activity

    @staticmethod
    def get_by_entity(entity_type, entity_id):
        return AuditLog.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id,
        ).order_by(
            AuditLog.audit_log_id.desc()
        ).all()