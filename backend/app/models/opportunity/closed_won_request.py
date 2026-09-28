from app.database import db
from app.models.base import BaseModel


class ClosedWonRequest(BaseModel):
    """Authoritative closure request record for Closed Won/Lost approval."""
    __tablename__ = "closed_won_requests"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('Pending', 'Approved', 'Rejected')",
            name="ck_closed_won_requests_status",
        ),
        db.CheckConstraint(
            "requested_outcome IN ('Closed Won', 'Closed Lost')",
            name="ck_closed_won_requests_outcome",
        ),
    )

    request_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )
    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    requested_active_role = db.Column(db.String(100), nullable=False)
    requested_outcome = db.Column(db.String(20), nullable=False, default="Closed Won", index=True)
    requested_reason = db.Column(db.Text, nullable=True)
    requested_explanation = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Pending", index=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    resolved_active_role = db.Column(db.String(100), nullable=True)
    resolution_reason = db.Column(db.Text, nullable=True)
    requested_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    opportunity = db.relationship("Opportunity", back_populates="closed_won_requests")
    requester = db.relationship("User", foreign_keys=[requested_by])
    resolver = db.relationship("User", foreign_keys=[resolved_by])
