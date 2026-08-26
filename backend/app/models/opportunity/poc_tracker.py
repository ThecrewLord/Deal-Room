from app.database import db
from app.models.base import BaseModel


class POCTracker(BaseModel):
    __tablename__ = "poc_tracker"

    poc_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )

    poc_name = db.Column(
        db.String(150),
        nullable=False,
    )

    start_date = db.Column(
        db.Date,
    )

    end_date = db.Column(
        db.Date,
    )

    status = db.Column(
        db.String(50),
        default="Draft",
        nullable=False,
        index=True,
    )

    remarks = db.Column(
        db.Text,
    )

    # Mandatory exit-criteria fields
    objective = db.Column(
        db.Text,
        nullable=False,
    )

    success_metric = db.Column(
        db.Text,
        nullable=False,
    )

    target_date = db.Column(
        db.Date,
        nullable=False,
    )

    failure_condition = db.Column(
        db.Text,
        nullable=False,
    )

    stakeholder_signoff = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    outcome = db.Column(
        db.String(20),
        nullable=True,
    )

    outcome_notes = db.Column(
        db.Text,
        nullable=True,
    )



    # Phase 6: separate technical design from execution/result.
    exit_criteria = db.Column(db.Text, nullable=True)
    poc_access_link = db.Column(db.Text, nullable=True)

    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)
    approved_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    submitted_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)
    submitted_at = db.Column(db.DateTime, nullable=True)

    requester = db.relationship("User", foreign_keys=[requested_by])
    approver = db.relationship("User", foreign_keys=[approved_by])
    submitter = db.relationship("User", foreign_keys=[submitted_by])

    opportunity = db.relationship(
        "Opportunity",
        back_populates="poc_trackers",
    )

    def __repr__(self):
        return f"<POCTracker {self.poc_name}>"