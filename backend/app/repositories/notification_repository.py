from app.database import db
from app.models.system.notification import Notification


class NotificationRepository:
    @staticmethod
    def create(notification):
        db.session.add(notification)
        return notification

    @staticmethod
    def get_for_user(user_id, unread_only=False):
        query = Notification.query.filter_by(recipient_user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(Notification.created_at.desc()).all()
