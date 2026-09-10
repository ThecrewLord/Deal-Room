from app.database import db
from app.models.base import BaseModel


class POCAssignment(BaseModel):
    __tablename__ = "poc_assignments"

    assignment_id = db.Column(db.Integer, primary_key=True)

    poc_id = db.Column(
        db.Integer,
        db.ForeignKey("poc_tracker.poc_id"),
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

    poc = db.relationship(
        "POCTracker",
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
            "poc_id",
            "user_id",
            name="uq_poc_assignment_user",
        ),
    )

    def __repr__(self):
        return (
            f"<POCAssignment("
            f"poc={self.poc_id}, "
            f"user={self.user_id}, "
            f"active={self.is_active})>"
        )