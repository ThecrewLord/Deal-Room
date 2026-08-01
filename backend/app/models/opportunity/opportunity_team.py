from app.database import db
from app.models.base import BaseModel


class OpportunityTeam(BaseModel):
    __tablename__ = "opportunity_team"

    team_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    role = db.Column(
        db.String(100),
        nullable=False,
    )

    opportunity = db.relationship(
        "Opportunity",
        back_populates="team_members",
    )

    user = db.relationship(
        "User",
    )

    def __repr__(self):
        return (
            f"<OpportunityTeam(opportunity={self.opportunity_id}, "
            f"user={self.user_id})>"
        )