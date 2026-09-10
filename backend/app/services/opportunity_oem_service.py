from app.auth.authorization import (
    AuthorizationService,
)
from app.database import db
from app.models.opportunity.opportunity_oem import OpportunityOEM
from app.repositories.opportunity_oem_repository import (
    OpportunityOEMRepository,
)
from app.repositories.oem_repository import OEMRepository
from app.repositories.opportunity_repository import OpportunityRepository


class OpportunityOEMService:

    @staticmethod
    def get_for_opportunity(
        opportunity_id,
        user,
        active_role,
    ):
        opportunity = OpportunityRepository.get_by_id(
            opportunity_id
        )

        if not AuthorizationService.can_view_opportunity(
            user,
            active_role,
            opportunity,
        ):
            return None

        return OpportunityOEMRepository.get_by_opportunity(
            opportunity_id
        )

    @staticmethod
    def add_oem(
        opportunity_id,
        oem_partner_id,
        user,
        active_role,
    ):
        opportunity = OpportunityRepository.get_by_id(
            opportunity_id
        )

        if not opportunity:
            raise LookupError("Opportunity not found.")

        if not AuthorizationService.can_view_opportunity(
            user,
            active_role,
            opportunity,
        ):
            raise PermissionError(
                "You are not authorized to access this opportunity."
            )

        oem = OEMRepository.get_by_id(oem_partner_id)

        if not oem:
            raise LookupError("OEM Partner not found.")

        if not AuthorizationService.can_view_oem(
            user,
            active_role,
            oem,
        ):
            raise PermissionError(
                "You are not authorized to access this OEM partner."
            )

        existing = OpportunityOEMRepository.get_by_pair(
            opportunity_id,
            oem_partner_id,
        )

        if existing:
            raise ValueError(
                "This OEM partner is already associated with the opportunity."
            )

        association = OpportunityOEM(
            opportunity_id=opportunity_id,
            oem_partner_id=oem_partner_id,
        )

        return OpportunityOEMRepository.create(
            association
        )

    @staticmethod
    def remove_oem(
        opportunity_id,
        oem_partner_id,
        user,
        active_role,
    ):
        opportunity = OpportunityRepository.get_by_id(
            opportunity_id
        )

        if not opportunity:
            raise LookupError("Opportunity not found.")

        if not AuthorizationService.can_view_opportunity(
            user,
            active_role,
            opportunity,
        ):
            raise PermissionError(
                "You are not authorized to access this opportunity."
            )

        oem = OEMRepository.get_by_id(oem_partner_id)

        if not oem:
            raise LookupError("OEM Partner not found.")

        if not AuthorizationService.can_view_oem(
            user,
            active_role,
            oem,
        ):
            raise PermissionError(
                "You are not authorized to access this OEM partner."
            )

        association = OpportunityOEMRepository.get_by_pair(
            opportunity_id,
            oem_partner_id,
        )

        if not association:
            raise LookupError(
                "OEM association not found."
            )

        OpportunityOEMRepository.delete(
            association
        )

        return True
