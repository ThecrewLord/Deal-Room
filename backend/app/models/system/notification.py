from app.models.base import BaseModel
from app.database import db


class Notification(BaseModel):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True)
    recipient_user_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True
    )
    notification_type = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)

    recipient = db.relationship("User", foreign_keys=[recipient_user_id])

    def to_dict(self):
        return {
            "notification_id": self.notification_id,
            "notification_type": self.notification_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at,
        }
