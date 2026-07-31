from app.database import db
from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    audit_log_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    entity_type = db.Column(
        db.String(50),
        nullable=False,
    )

    entity_id = db.Column(
        db.Integer,
        nullable=False,
    )

    action = db.Column(
        db.String(100),
        nullable=False,
    )

    description = db.Column(
        db.Text,
    )

    performed_by = db.Column(
        db.Integer,
        nullable=True,
    )