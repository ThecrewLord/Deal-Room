from app.database import db
from app.models.base import BaseModel


class ClosedWonRequest(BaseModel):
    """Single pending/terminal Closed Won request for an opportunity."""
    __tablename__ = "closed_won_requests"
    __table_args__ = (
        db.UniqueConstraint("opportunity_id", name="uq_closed_won_requests_opportunity"),
        db.CheckConstraint(
            "status IN ('Pending', 'Approved', 'Rejected')",
            name="ck_closed_won_requests_status",
        ),
    )

    request_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )
    requested_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
    )
    requested_active_role = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending", index=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    resolved_active_role = db.Column(db.String(100), nullable=True)
    resolution_reason = db.Column(db.Text, nullable=True)
    requested_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    resolved_at = db.Column(db.DateTime, nullable=True)

    opportunity = db.relationship("Opportunity", back_populates="closed_won_request")
    requester = db.relationship("User", foreign_keys=[requested_by])
    resolver = db.relationship("User", foreign_keys=[resolved_by])
