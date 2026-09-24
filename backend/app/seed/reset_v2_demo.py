"""Explicit development/demo reset for Deal Room V2 business data.

Never run this command against production. Authentication identities, roles,
permissions and security configuration are deliberately preserved.
"""
from app.database import db
from app.models.opportunity.closed_won_request import ClosedWonRequest
from app.models.opportunity.opportunity_value_history import OpportunityValueHistory
from app.models.opportunity.stage_history import StageHistory
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.solution_design import SolutionDesign
from app.models.opportunity.opportunity import Opportunity
from app.models.phase2 import OEMOpportunity, RFXContext, NegotiationContext, POCTeamMember, DeliveryProjectMember, DeliveryProject, Activity, FollowUp


def reset_v2_demo_data():
    """Reset disposable opportunity/demo data without weakening runtime guards.

    Value history is intentionally append-only during normal application use.
    The explicit development reset is the one controlled exception: the
    PostgreSQL trigger is removed for the duration of this transaction and
    recreated before commit. Authentication/security data is never touched.
    """
    connection = db.session.connection()
    dialect = connection.dialect.name
    trigger_was_disabled = False

    try:
        if dialect == "postgresql":
            connection.exec_driver_sql(
                "DROP TRIGGER IF EXISTS trg_opportunity_value_history_append_only "
                "ON opportunity_value_history"
            )
            trigger_was_disabled = True

        for model in (
            Activity,
            FollowUp,
            DeliveryProjectMember,
            DeliveryProject,
            POCTeamMember,
            OEMOpportunity,
            NegotiationContext,
            RFXContext,
            ClosedWonRequest,
            OpportunityValueHistory,
            StageHistory,
            OpportunityTeam,
            Stakeholder,
            POCTracker,
            SolutionDesign,
            Opportunity,
        ):
            db.session.query(model).delete(synchronize_session=False)

        if dialect == "postgresql" and trigger_was_disabled:
            connection.exec_driver_sql("""
                CREATE TRIGGER trg_opportunity_value_history_append_only
                BEFORE UPDATE OR DELETE ON opportunity_value_history
                FOR EACH ROW EXECUTE FUNCTION prevent_opportunity_value_history_mutation();
            """)

        db.session.commit()
    except Exception:
        db.session.rollback()
        # Restore the guard if the reset failed after dropping it.  This is
        # deliberately best-effort; the original trigger/function remain the
        # authoritative protection and should never be left disabled.
        if dialect == "postgresql" and trigger_was_disabled:
            try:
                connection = db.session.connection()
                connection.exec_driver_sql("""
                    CREATE TRIGGER trg_opportunity_value_history_append_only
                    BEFORE UPDATE OR DELETE ON opportunity_value_history
                    FOR EACH ROW EXECUTE FUNCTION prevent_opportunity_value_history_mutation();
                """)
                db.session.commit()
            except Exception:
                db.session.rollback()
        raise
