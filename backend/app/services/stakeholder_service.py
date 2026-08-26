from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.repositories.stakeholder_repository import StakeholderRepository
from app.services.activity_service import ActivityService
from app.constants.activity_types import STAKEHOLDER_CREATED, STAKEHOLDER_UPDATED
from app.database import db


class StakeholderService:
    @staticmethod
    def create_stakeholder(data, user, active_role):
        opportunity = StakeholderRepository.get_opportunity(data["opportunity_id"])
        if not AuthorizationService.can_mutate_related(user, active_role, opportunity, "stakeholder", "create"):
            raise AuthorizationDenied("You are not authorized to create stakeholders for this opportunity.")
        stakeholder = StakeholderRepository.create(data)
        ActivityService.log(
            "Stakeholder", stakeholder.stakeholder_id, STAKEHOLDER_CREATED,
            f"Stakeholder '{stakeholder.stakeholder_name}' created.",
            user.user_id,
            commit=False,
        )
        db.session.commit()
        return stakeholder

    @staticmethod
    def get_by_id(stakeholder_id, user, active_role):
        stakeholder = StakeholderRepository.get_by_id(stakeholder_id)
        if not AuthorizationService.can_view_stakeholder(user, active_role, stakeholder):
            return None
        return stakeholder

    @staticmethod
    def get_by_opportunity(opportunity_id, user, active_role):
        opportunity = StakeholderRepository.get_opportunity(opportunity_id)
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return []
        return StakeholderRepository.get_by_opportunity(opportunity_id)

    @staticmethod
    def update_stakeholder(stakeholder_id, data, user, active_role):
        stakeholder = StakeholderRepository.get_by_id(stakeholder_id)
        if not stakeholder:
            return None
        if not AuthorizationService.can_mutate_related(user, active_role, stakeholder.opportunity, "stakeholder", "update"):
            raise AuthorizationDenied("You are not authorized to update this stakeholder.")
        incoming_updated_at = data.pop("updated_at", None)
        if incoming_updated_at and stakeholder.updated_at:
            if incoming_updated_at.replace(tzinfo=None) != stakeholder.updated_at.replace(tzinfo=None):
                raise RuntimeError("This stakeholder was updated by someone else. Please reload and try again.")
        updated = StakeholderRepository.update(stakeholder, data)
        ActivityService.log(
            "Stakeholder", stakeholder.stakeholder_id, STAKEHOLDER_UPDATED,
            f"Stakeholder '{stakeholder.stakeholder_name}' updated.",
            user.user_id,
            commit=False,
        )
        db.session.commit()
        return updated

    @staticmethod
    def delete_stakeholder(stakeholder_id, user, active_role):
        stakeholder = StakeholderRepository.get_by_id(stakeholder_id)
        if not stakeholder:
            return False
        if not AuthorizationService.can_mutate_related(user, active_role, stakeholder.opportunity, "stakeholder", "delete"):
            raise AuthorizationDenied("You are not authorized to delete this stakeholder.")
        return StakeholderRepository.delete(stakeholder)
