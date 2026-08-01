from app.database import db
from app.models.base import BaseModel


class Opportunity(BaseModel):
    __tablename__ = "opportunities"

    opportunity_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    account_id = db.Column(
        db.Integer,
        db.ForeignKey("accounts.account_id"),
        nullable=False,
        index=True,
    )

    stage_id = db.Column(
        db.Integer,
        db.ForeignKey("stage_master.stage_id"),
        nullable=False,
        index=True,
    )

    opportunity_name = db.Column(
        db.String(200),
        nullable=False,
    )

    description = db.Column(
        db.Text,
    )

    estimated_value = db.Column(
        db.Numeric(15, 2),
        default=0,
    )

    probability = db.Column(
        db.Integer,
        default=0,
    )

    expected_close_date = db.Column(
        db.Date,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Open",
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
    )

    poc_trackers = db.relationship(
        "POCTracker",
        back_populates="opportunity",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def __repr__(self):
        return (
            f"<Opportunity(opportunity_id={self.opportunity_id}, "
            f"name='{self.opportunity_name}')>"
        )