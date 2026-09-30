from app.database import db
from app.models.opportunity.poc_history import POCHistory, POC_HISTORY_EVENT_TYPES
from app.models.opportunity.opportunity import Opportunity


class POCHistoryService:
    """Persistence helper for immutable POC business history.

    This helper never commits. The calling domain action owns the transaction,
    so history is committed or rolled back with the POC mutation that caused it.
    """

    @staticmethod
    def record_poc_history(opportunity_id, actor, event_type, reason=None):
        if event_type not in POC_HISTORY_EVENT_TYPES:
            raise ValueError(f"Unsupported POC history event type: {event_type}")
        if not getattr(actor, "user_id", None):
            raise ValueError("A valid authenticated actor is required.")
        if not db.session.get(Opportunity, opportunity_id):
            raise ValueError("Opportunity not found.")

        if event_type == "NEW_POC_REQUESTED":
            normalized_reason = str(reason or "").strip()
            if not normalized_reason:
                raise ValueError("reason is required for NEW_POC_REQUESTED history.")
            reason = normalized_reason
        elif reason is not None:
            reason = str(reason).strip() or None

        history = POCHistory(
            opportunity_id=opportunity_id,
            actor_id=actor.user_id,
            event_type=event_type,
            reason=reason,
        )
        db.session.add(history)
        return history

    @staticmethod
    def get_for_opportunity(opportunity_id):
        return (
            POCHistory.query
            .filter_by(opportunity_id=opportunity_id)
            .order_by(POCHistory.created_at.asc(), POCHistory.history_id.asc())
            .all()
        )
