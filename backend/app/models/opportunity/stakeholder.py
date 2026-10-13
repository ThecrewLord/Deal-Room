from app.database import db
from app.models.base import BaseModel
from sqlalchemy.orm import synonym

stakeholder_tag_links = db.Table(
    "stakeholder_tag_links",
    db.Column("stakeholder_id", db.Integer, db.ForeignKey("stakeholders.stakeholder_id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.tag_id", ondelete="RESTRICT"), primary_key=True),
)

class Stakeholder(BaseModel):
    __tablename__ = "stakeholders"
    __table_args__ = (
        db.Index(
            "uq_stakeholder_decision_maker_per_opportunity",
            "opportunity_id",
            unique=True,
            postgresql_where=db.text("is_decision_maker = TRUE"),
            sqlite_where=db.text("is_decision_maker = 1"),
        ),
    )
    stakeholder_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(200))
    is_decision_maker = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)
    opportunity = db.relationship("Opportunity", back_populates="stakeholders")
    tags = db.relationship("Tag", secondary=stakeholder_tag_links, lazy="selectin")
    stakeholder_name = synonym("name")
    designation = synonym("job_title")
    @property
    def influence_level(self): return "Decision Maker" if self.is_decision_maker else None
    def __repr__(self): return f"<Stakeholder {self.name}>"
