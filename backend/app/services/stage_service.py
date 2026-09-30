"""Stage read/compatibility facade.

All v2 mutations are delegated to LifecycleTransitionService.  This module
exists to preserve imports used by older reporting/POC code during cutover.
"""
from app.constants.stages import INITIAL_STAGE_NAME, LIFECYCLE_STAGES
from app.repositories.stage_repository import StageRepository
from app.services.lifecycle_transition_service import LifecycleTransitionService


class StageService:
    @staticmethod
    def get_initial_stage():
        return StageRepository.get_by_name(INITIAL_STAGE_NAME)

    @staticmethod
    def get_all():
        return StageRepository.get_all()

    @staticmethod
    def get_by_id(stage_id):
        return StageRepository.get_by_id(stage_id)

    @staticmethod
    def record_initial_stage(opportunity, user_id, remarks="Opportunity created."):
        # Initial creation is not a transition; retain the baseline history row.
        return StageRepository.add_history(
            opportunity_id=opportunity.opportunity_id,
            stage_id=opportunity.stage_id,
            changed_by=user_id,
            remarks=remarks,
            from_lifecycle_stage=None,
            to_lifecycle_stage=getattr(opportunity, "lifecycle_stage", "Lead"),
            version=getattr(opportunity, "row_version", 1),
        )

    @staticmethod
    def transition_stage(opportunity, target_stage_id, user, active_role, remarks=None):
        target = StageRepository.get_by_id(target_stage_id)
        if not target:
            raise ValueError("Invalid opportunity stage.")
        # Legacy callers must use the canonical v2 lifecycle names. A raw
        # stage-id mutation is deliberately no longer supported.
        lifecycle = target.stage_name
        if lifecycle not in LIFECYCLE_STAGES:
            raise ValueError("The supplied stage is not a canonical V2 lifecycle stage.")
        return LifecycleTransitionService.transition(
            opportunity.opportunity_id,
            lifecycle,
            opportunity.row_version,
            user,
            active_role,
            remarks=remarks,
        )

    @staticmethod
    def transition_technical_stage(opportunity_id, target_stage_name, expected_version, remarks, user, active_role):
        lifecycle = target_stage_name
        return LifecycleTransitionService.transition(
            opportunity_id, lifecycle, expected_version, user, active_role, remarks=remarks
        )

    @staticmethod
    def close_opportunity(opportunity_id, won, reason, expected_version, user, active_role):
        if won:
            return LifecycleTransitionService.close_won(opportunity_id, expected_version, user, active_role)
        return LifecycleTransitionService.close_lost(opportunity_id, expected_version, reason, None, user, active_role)

    @staticmethod
    def get_history(opportunity_id):
        return StageRepository.get_history(opportunity_id)
