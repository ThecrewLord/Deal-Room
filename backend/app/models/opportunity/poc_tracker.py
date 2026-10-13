from app.database import db
from app.models.base import BaseModel


class POCTracker(BaseModel):
    __tablename__ = "poc_tracker"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('Draft','In Progress','Submitted','Completed')",
            name="ck_poc_tracker_status",
        ),
        db.CheckConstraint(
            "outcome IS NULL OR outcome IN ('Success','Failure','Ongoing','Abandoned')",
            name="ck_poc_tracker_outcome",
        ),
        db.CheckConstraint(
            "row_version >= 1",
            name="ck_poc_tracker_row_version_positive",
        ),
    )

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

    row_version = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1",
        index=True,
    )

    remarks = db.Column(
        db.Text,
    )

    # POC workflow metadata. Requirement/document content belongs in the external RFX Drive workspace.
    target_date = db.Column(
        db.Date,
        nullable=False,
    )

    outcome = db.Column(
        db.String(20),
        nullable=True,
    )

    result_view_link = db.Column(db.Text, nullable=True)
    submission_metadata = db.Column(db.JSON, nullable=True)
    outcome_notes = db.Column(
        db.Text,
        nullable=True,
    )


    # POC creator and execution audit fields. No manager approval workflow.
    requested_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)

    submitted_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)
    submitted_at = db.Column(db.DateTime, nullable=True)

    requester = db.relationship("User", foreign_keys=[requested_by])
    submitter = db.relationship("User", foreign_keys=[submitted_by])
    team_members = db.relationship("POCTeamMember", backref="poc", cascade="all, delete-orphan", lazy=True)

    opportunity = db.relationship(
        "Opportunity",
        back_populates="poc_trackers",
    )

    def __repr__(self):
        return f"<POCTracker {self.poc_name}>"