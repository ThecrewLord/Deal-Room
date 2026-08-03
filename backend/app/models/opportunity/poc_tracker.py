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
        default="Planned",
        nullable=False,
    )

    remarks = db.Column(
        db.Text,
    )

    # --- Mandatory exit-criteria fields (core project requirement) ---

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
    )  # Success / Failure / Ongoing / Abandoned

    outcome_notes = db.Column(
        db.Text,
        nullable=True,
    )

    opportunity = db.relationship(
        "Opportunity",
        back_populates="poc_trackers",
    )

    def __repr__(self):
        return f"<POCTracker {self.poc_name}>"