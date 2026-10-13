from app.database import db
from app.models.base import BaseModel


class StageHistory(BaseModel):
    __tablename__ = "stage_history"

    history_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey("opportunities.opportunity_id"), nullable=False, index=True)

    # Legacy stage id is preserved for compatibility/history lookup.
    stage_id = db.Column(db.Integer, db.ForeignKey("stage_master.stage_id"), nullable=False, index=True)
    from_lifecycle_stage = db.Column(db.String(30), nullable=True)
    to_lifecycle_stage = db.Column(db.String(30), nullable=True)
    actor_active_role = db.Column(db.String(50), nullable=True)
    version = db.Column(db.Integer, nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    remarks = db.Column(db.Text)

    opportunity = db.relationship("Opportunity", back_populates="stage_history")
    stage = db.relationship("StageMaster", back_populates="stage_history")
    user = db.relationship("User")

    def __repr__(self):
        return f"<StageHistory(opportunity={self.opportunity_id}, stage={self.stage_id})>"
