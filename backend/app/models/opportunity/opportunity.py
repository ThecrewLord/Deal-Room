from app.database import db
from app.models.base import BaseModel


class Opportunity(BaseModel):
    __tablename__ = "opportunities"

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
    estimated_value = db.Column(db.Numeric(15, 2), default=0)
    probability = db.Column(db.Integer, default=0)
    expected_close_date = db.Column(db.Date)

    # Status describes operational state; stage describes lifecycle position.
    status = db.Column(
        db.String(50),
        nullable=False,
        default="Open",
        index=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

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
        """Expose operational workflow state without adding a duplicate state column."""
        if self.status == "Approved" and self.sales_owner_id is not None:
            has_technical_team = any(
                member.role == "Solution Engineer"
                for member in self.team_members
            )
            if not has_technical_team:
                return "Approved / Awaiting Pre-Sales Assignment"
            return "Approved"
        if self.status == "Active":
            return "Pre-Sales Assignment Complete / Active Technical Work"
        if self.status in {
            "Pending Sales Manager Review",
            "Rejected",
        }:
            return self.status
        if self.current_stage is None:
            return None
        return self.current_stage.stage_name

    def __repr__(self):
        return (
            f"<Opportunity(opportunity_id={self.opportunity_id}, "
            f"name='{self.opportunity_name}')>"
        )
