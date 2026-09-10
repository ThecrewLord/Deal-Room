from app.database import db
from app.models.base import BaseModel


class DeliveryAssignment(BaseModel):
    __tablename__ = "delivery_assignments"

    assignment_id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("delivery_projects.project_id"),
        nullable=False,
        index=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    assigned_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    role = db.Column(
        db.String(100),
        nullable=False,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    assigned_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    project = db.relationship(
        "DeliveryProject",
        back_populates="assignments",
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
    )

    assigner = db.relationship(
        "User",
        foreign_keys=[assigned_by],
    )

    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_delivery_assignment_user",
        ),
    )
