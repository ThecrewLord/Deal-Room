from app.database import db
from app.models.base import BaseModel


class Opportunity(BaseModel):
    __tablename__ = "opportunities"
    __table_args__ = (
        db.CheckConstraint("outcome IN ('Open','Closed Won','Closed Lost')", name="ck_opportunities_v2_outcome"),
        db.CheckConstraint("operational_status IN ('Active','Stalled','Closed')", name="ck_opportunities_v2_operational_status"),
        db.CheckConstraint("lifecycle_stage IS NULL OR lifecycle_stage IN ('Lead','Qualified','RFX','POC','Negotiations','Delivery')", name="ck_opportunities_v2_lifecycle_stage"),
        db.CheckConstraint("(outcome = 'Open' AND operational_status IN ('Active','Stalled')) OR (outcome IN ('Closed Won','Closed Lost') AND operational_status = 'Closed')", name="ck_opportunities_v2_closed_consistency"),
        db.CheckConstraint("final_revenue IS NULL OR final_revenue >= 0", name="ck_opportunities_final_revenue_non_negative"),
    )

    opportunity_id = db.Column(db.Integer, primary_key=True)

    account_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
    )

    # Distinct lifecycle ownership concepts.
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=True,
        index=True,
    )

    sales_owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=True,
        index=True,
    )

    stage_id = db.Column(
        db.Integer,
        db.ForeignKey("stage_master.stage_id"),
        nullable=False,
        index=True,
    )

    opportunity_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    pain_points = db.Column(db.Text)
    estimated_value = db.Column(db.Numeric(15, 2), default=0)
    final_revenue = db.Column(db.Numeric(15, 2), nullable=True)
    probability = db.Column(db.Integer, default=0)
    expected_close_date = db.Column(db.Date)

    # Status describes operational state; stage describes lifecycle position.
    # V2 state dimensions. These are authoritative; legacy stage_id/status/
    # is_active remain read-only compatibility fields during cutover.
    lifecycle_stage = db.Column(
        db.String(30), nullable=False, default="Lead", index=True
    )
    outcome = db.Column(
        db.String(20), nullable=False, default="Open", index=True
    )
    operational_status = db.Column(
        db.String(20), nullable=False, default="Active", index=True
    )
    review_status = db.Column(
        db.String(40), nullable=False, default="Draft", index=True
    )
    lost_reason = db.Column(db.String(100), nullable=True)
    lost_explanation = db.Column(db.Text, nullable=True)
    row_version = db.Column(
        db.Integer, nullable=False, default=1, server_default="1", index=True
    )

    # Legacy compatibility columns. Application workflow code must not use
    # these as the source of truth for v2 state.
    status = db.Column(
        db.String(50), nullable=False, default="Open", index=True
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    account = db.relationship(
        "Account",
        back_populates="opportunities",
    )

    created_by_user = db.relationship(
        "User",
        foreign_keys=[created_by],
    )

    sales_owner = db.relationship(
        "User",
        foreign_keys=[sales_owner_id],
    )

    current_stage = db.relationship(
        "StageMaster",
        back_populates="opportunities",
    )

    stakeholders = db.relationship(
        "Stakeholder",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        lazy=True,
    )

    team_members = db.relationship(
        "OpportunityTeam",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        lazy=True,
    )

    closed_won_request = db.relationship(
        "ClosedWonRequest",
        back_populates="opportunity",
        uselist=False,
        cascade="all, delete-orphan",
    )

    value_history = db.relationship(
        "OpportunityValueHistory",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="OpportunityValueHistory.changed_at",
    )

    stage_history = db.relationship(
        "StageHistory",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="StageHistory.created_at",
    )

    poc_trackers = db.relationship(
        "POCTracker",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        lazy=True,
    )

    solution_design = db.relationship(
        "SolutionDesign",
        back_populates="opportunity",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def lifecycle_state(self):
        """Backward-compatible label; v2 clients should use explicit fields."""
        return self.lifecycle_stage

    @property
    def is_closed(self):
        return self.operational_status == "Closed"

    def __repr__(self):
        return (
            f"<Opportunity(opportunity_id={self.opportunity_id}, "
            f"name='{self.opportunity_name}')>"
        )
