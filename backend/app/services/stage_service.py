from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.roles import SALES_EXECUTIVE, SOLUTION_ENGINEER
from app.constants.stages import (
    CLOSED_STATUS, OPEN_STATUS, REJECTED_STATUS,
    PENDING_SALES_MANAGER_REVIEW_STATUS, APPROVED_STATUS, ACTIVE_STATUS,
)
from app.constants.activity_types import OPPORTUNITY_STAGE_CHANGED, OPPORTUNITY_CLOSED_WON, OPPORTUNITY_CLOSED_LOST
from app.database import db
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.stage_history import StageHistory
from app.repositories.stage_repository import StageRepository
from app.services.activity_service import ActivityService
from app.utils.concurrency import ConcurrencyManager


TECHNICAL_TRANSITIONS = {
    "Qualification": {"Discovery"},
    "Discovery": {"POC / Technical Evaluation", "Proposal"},
    "POC / Technical Evaluation": {"Proposal"},
    "Proposal": {"Negotiation"},
    "Negotiation": {"Closed Won", "Closed Lost"},
}


class StageService:
    @staticmethod
    def get_initial_stage():
        return StageRepository.get_by_name("Lead / Identified")

    @staticmethod
    def record_initial_stage(opportunity, user_id, remarks="Opportunity created."):
        return StageRepository.add_history(
            opportunity_id=opportunity.opportunity_id,
            stage_id=opportunity.stage_id,
            changed_by=user_id,
            remarks=remarks,
        )

    @staticmethod
    def transition_stage(opportunity, target_stage_id, user, active_role, remarks=None):
        # Preserve the Phase 3 Sales Executive qualification action.
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            raise AuthorizationDenied("You are not authorized to modify this opportunity.")
        target = StageRepository.get_by_id(target_stage_id)
        current = opportunity.current_stage
        if not target or not current:
            raise ValueError("Invalid opportunity stage.")
        if target.stage_id == current.stage_id:
            return opportunity
        if active_role == SALES_EXECUTIVE and current.stage_name == "Lead / Identified" and target.stage_name == "Qualification":
            opportunity.stage_id = target.stage_id
            opportunity.status = OPEN_STATUS
            opportunity.is_active = True
            StageRepository.add_history(opportunity.opportunity_id, target.stage_id, user.user_id, remarks)
            db.session.commit()
            return opportunity
        raise AuthorizationDenied("This stage transition must use an explicit technical business action.")

    @staticmethod
    def transition_technical_stage(opportunity_id, target_stage_name, updated_at, remarks, user, active_role):
        from app.repositories.opportunity_repository import OpportunityRepository
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        if not AuthorizationService.can_change_technical_stage(user, active_role, opportunity):
            raise AuthorizationDenied("Only an assigned Solution Engineer can change technical stage.")
        if not opportunity.is_active or opportunity.status != ACTIVE_STATUS:
            raise ValueError("Opportunity is not in active technical work.")
        if ConcurrencyManager.has_conflict(updated_at, opportunity.updated_at):
            raise RuntimeError("Opportunity changed since it was opened. Refresh before changing stage.")
        target = StageRepository.get_by_name(target_stage_name)
        current = opportunity.current_stage
        if not target or not current:
            raise ValueError("Invalid opportunity stage.")
        allowed = TECHNICAL_TRANSITIONS.get(current.stage_name, set())
        if target.stage_name not in allowed:
            raise ValueError(f"Transition from {current.stage_name} to {target.stage_name} is not allowed.")
        if target.stage_name == "POC / Technical Evaluation":
            from app.models.opportunity.poc_tracker import POCTracker
            from app.constants.poc_outcome import POC_STATUS_APPROVED, POC_STATUS_IN_PROGRESS
            approved_poc = POCTracker.query.filter_by(
                opportunity_id=opportunity.opportunity_id, status=POC_STATUS_APPROVED
            ).first()
            in_progress = POCTracker.query.filter_by(
                opportunity_id=opportunity.opportunity_id, status=POC_STATUS_IN_PROGRESS
            ).first()
            if not approved_poc and not in_progress:
                raise ValueError("An approved POC is required before entering POC / Technical Evaluation.")
        if current.stage_name == "POC / Technical Evaluation" and target.stage_name == "Proposal":
            from app.models.opportunity.poc_tracker import POCTracker
            from app.constants.poc_outcome import POC_STATUS_COMPLETED
            completed_poc = POCTracker.query.filter_by(
                opportunity_id=opportunity.opportunity_id, status=POC_STATUS_COMPLETED
            ).first()
            if not completed_poc:
                raise ValueError("A completed POC review is required before moving to Proposal.")
        if target.is_closed:
            opportunity.status = CLOSED_STATUS
            opportunity.is_active = False
        else:
            opportunity.status = ACTIVE_STATUS
            opportunity.is_active = True
        opportunity.stage_id = target.stage_id
        StageRepository.add_history(opportunity.opportunity_id, target.stage_id, user.user_id, remarks)
        ActivityService.log(
            "Opportunity", opportunity.opportunity_id, OPPORTUNITY_STAGE_CHANGED,
            f"Stage changed from '{current.stage_name}' to '{target.stage_name}'.",
            user.user_id, commit=False,
        )
        db.session.commit()
        return opportunity

    @staticmethod
    def close_opportunity(opportunity_id, won, remarks, updated_at, user, active_role):
        from app.repositories.opportunity_repository import OpportunityRepository
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        if not AuthorizationService.can_close_opportunity(user, active_role, opportunity):
            raise AuthorizationDenied("Only an assigned Solution Engineer can close this opportunity.")
        if not opportunity.is_active or opportunity.status != ACTIVE_STATUS:
            raise ValueError("Opportunity is not active.")
        if ConcurrencyManager.has_conflict(updated_at, opportunity.updated_at):
            raise RuntimeError("Opportunity changed since it was opened. Refresh before closing.")
        if opportunity.current_stage is None or opportunity.current_stage.stage_name != "Negotiation":
            raise ValueError("Opportunity can only be closed from Negotiation.")
        target_name = "Closed Won" if won else "Closed Lost"
        target = StageRepository.get_by_name(target_name)
        if not target:
            raise RuntimeError(f"Required stage '{target_name}' is not configured.")
        opportunity.stage_id = target.stage_id
        opportunity.status = CLOSED_STATUS
        opportunity.is_active = False
        StageRepository.add_history(
            opportunity.opportunity_id, target.stage_id, user.user_id,
            remarks or f"Opportunity closed {'Won' if won else 'Lost'}.",
        )
        ActivityService.log(
            "Opportunity", opportunity.opportunity_id,
            OPPORTUNITY_CLOSED_WON if won else OPPORTUNITY_CLOSED_LOST,
            remarks or f"Opportunity closed {'Won' if won else 'Lost'}.",
            user.user_id, commit=False,
        )
        db.session.commit()
        return opportunity

    @staticmethod
    def get_history(opportunity_id):
        return StageRepository.get_history(opportunity_id)
