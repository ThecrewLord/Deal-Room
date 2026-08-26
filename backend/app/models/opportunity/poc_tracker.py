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


    outcome = db.Column(
        db.String(20),
        nullable=True,
    )

    outcome_notes = db.Column(
        db.Text,
        nullable=True,
    )


    # POC creator and execution audit fields. No manager approval workflow.
    exit_criteria = db.Column(db.Text, nullable=True)
    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)

    submitted_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)
    submitted_at = db.Column(db.DateTime, nullable=True)

    requester = db.relationship("User", foreign_keys=[requested_by])
    submitter = db.relationship("User", foreign_keys=[submitted_by])

    opportunity = db.relationship(
        "Opportunity",
        back_populates="poc_trackers",
    )

    def __repr__(self):
        return f"<POCTracker {self.poc_name}>"