from app.database import db
from app.models.base import BaseModel


class OpportunityValueHistory(BaseModel):
    """Append-only record of Opportunity Value mutations."""

    __tablename__ = "opportunity_value_history"

    history_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id"),
        nullable=False,
        index=True,
    )
    old_value = db.Column(db.Numeric(15, 2), nullable=True)
    new_value = db.Column(db.Numeric(15, 2), nullable=False)
    reason = db.Column(db.String(2000), nullable=False)
    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )
    actor_active_role = db.Column(db.String(100), nullable=False, index=True)
    changed_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        index=True,
    )
    opportunity_row_version = db.Column(db.Integer, nullable=False)

    opportunity = db.relationship("Opportunity", back_populates="value_history")
    actor = db.relationship("User")

    __table_args__ = (
        db.CheckConstraint("new_value >= 0", name="ck_opportunity_value_history_new_non_negative"),
        db.CheckConstraint("old_value IS NULL OR old_value >= 0", name="ck_opportunity_value_history_old_non_negative"),
    )
