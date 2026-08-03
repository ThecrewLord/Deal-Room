from app.database import db
from app.models.base import BaseModel


class Stakeholder(BaseModel):
    __tablename__ = "stakeholders"

    stakeholder_id = db.Column(
        db.Integer,
        primary_key=True,
    )

    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )

    stakeholder_name = db.Column(
        db.String(150),
        nullable=False,
    )

    designation = db.Column(
        db.String(150),
    )

    email = db.Column(
        db.String(150),
    )

    phone = db.Column(
        db.String(50),
    )

    influence_level = db.Column(
        db.String(50),
    )

    notes = db.Column(
        db.Text,
    )

    opportunity = db.relationship(
        "Opportunity",
        back_populates="stakeholders",
    )

    def __repr__(self):
        return f"<Stakeholder {self.stakeholder_name}>"