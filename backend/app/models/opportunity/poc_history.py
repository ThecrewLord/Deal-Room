from app.database import db
from sqlalchemy import event


POC_HISTORY_EVENT_TYPES = {
    "POC_STARTED",
    "POC_SUBMITTED",
    "NEW_POC_REQUESTED",
}


class POCHistory(db.Model):
    """Immutable business history for POC lifecycle events."""

    __tablename__ = "poc_history"
    __table_args__ = (
        db.CheckConstraint(
            "event_type IN ('POC_STARTED','POC_SUBMITTED','NEW_POC_REQUESTED')",
            name="ck_poc_history_event_type",
        ),
        db.CheckConstraint(
            "event_type <> 'NEW_POC_REQUESTED' OR "
            "(reason IS NOT NULL AND length(trim(reason)) > 0)",
            name="ck_poc_history_repeat_reason",
        ),
        db.Index(
            "ix_poc_history_opportunity_created_at",
            "opportunity_id",
            "created_at",
        ),
    )

    # Server-generated immutable event timestamp; no client-supplied value.
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    history_id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunities.opportunity_id", ondelete="RESTRICT"),
        nullable=False,
    )
    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type = db.Column(db.String(40), nullable=False)
    reason = db.Column(db.Text, nullable=True)

    opportunity = db.relationship("Opportunity", back_populates="poc_history")
    actor = db.relationship("User", foreign_keys=[actor_id])


@event.listens_for(POCHistory, "before_update")
def _reject_history_update(mapper, connection, target):
    raise ValueError("POC history records are immutable and cannot be updated.")


@event.listens_for(POCHistory, "before_delete")
def _reject_history_delete(mapper, connection, target):
    raise ValueError("POC history records are immutable and cannot be deleted.")
