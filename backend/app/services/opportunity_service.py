from datetime import datetime

from flask import current_app

from app.models.opportunity.opportunity import Opportunity
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.activity_service import ActivityService
from app.utils.concurrency import ConcurrencyManager


class OpportunityService:

    @staticmethod
    def create_opportunity(data):

        if OpportunityRepository.exists(
            data["opportunity_name"],
            data["account_id"],
        ):
            raise ValueError(
                "Opportunity already exists for this account."
            )

        opportunity = Opportunity(
            account_id=data["account_id"],
            stage_id=data["stage_id"],
            opportunity_name=data["opportunity_name"],
            description=data.get("description"),
            estimated_value=data.get("estimated_value", 0),
            probability=data.get("probability", 0),
            expected_close_date=data.get("expected_close_date"),
            status=data.get("status", "Open"),
            is_active=True,
        )

        opportunity = OpportunityRepository.create(opportunity)

        try:
            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action="CREATE_OPPORTUNITY",
                description=(
                    f"Opportunity '{opportunity.opportunity_name}' created."
                ),
            )
        except Exception:
            current_app.logger.exception(
                "Failed to log Opportunity creation activity."
            )

        return opportunity

    @staticmethod
    def get_all():
        return OpportunityRepository.get_all()

    @staticmethod
    def get_by_id(opportunity_id):
        return OpportunityRepository.get_by_id(opportunity_id)

    @staticmethod
    def update_opportunity(opportunity_id, data):
        opportunity = OpportunityRepository.get_by_id(
            opportunity_id
        )

        if not opportunity:
            return None

        client_timestamp = data.pop("updated_at")

        if isinstance(client_timestamp, str):
            client_timestamp = datetime.fromisoformat(
                client_timestamp.replace("Z", "+00:00")
            )

        if ConcurrencyManager.has_conflict(
            client_timestamp,
            opportunity.updated_at,
        ):
            raise RuntimeError(
                "This opportunity has been modified by another user. Please refresh and try again."
            )

        for key, value in data.items():
            if hasattr(opportunity, key):
                setattr(opportunity, key, value)

        OpportunityRepository.update()

        try:
            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action="UPDATE_OPPORTUNITY",
                description=(
                    f"Opportunity '{opportunity.opportunity_name}' updated."
                ),
            )
        except Exception:
            current_app.logger.exception(
                "Failed to log Opportunity update activity."
            )

        return opportunity

    @staticmethod
    def search(search_term):
        return OpportunityRepository.search(search_term)
    def delete_opportunity(opportunity_id):

        opportunity = OpportunityRepository.get_by_id(
            opportunity_id
        )

        if not opportunity:
            return False

        OpportunityRepository.delete(opportunity)

        try:
            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action="DELETE_OPPORTUNITY",
                description=(
                    f"Opportunity '{opportunity.opportunity_name}' deleted."
                ),
            )
        except Exception:
            current_app.logger.exception(
                "Failed to log Opportunity delete activity."
            )

        return True