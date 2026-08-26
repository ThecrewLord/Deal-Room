from app.database import db
from app.models.base import BaseModel


class SolutionDesign(BaseModel):
    __tablename__ = "solution_designs"

    design_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        unique=True,
        index=False,
    )
    solution_summary = db.Column(db.Text)
    technical_approach = db.Column(db.Text)
    technical_requirements = db.Column(db.Text)
    architecture_notes = db.Column(db.Text)
    risks = db.Column(db.Text)
    assumptions = db.Column(db.Text)

    opportunity = db.relationship("Opportunity", back_populates="solution_design")

    def __repr__(self):
        return f"<SolutionDesign opportunity_id={self.opportunity_id}>"
