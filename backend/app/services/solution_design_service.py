from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.activity_types import SOLUTION_DESIGN_CREATED, SOLUTION_DESIGN_UPDATED
from app.database import db
from app.models.opportunity.solution_design import SolutionDesign
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.activity_service import ActivityService
from app.utils.concurrency import ConcurrencyManager


class SolutionDesignService:
    @staticmethod
    def get(opportunity_id, user, active_role):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity or not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return None
        return opportunity.solution_design

    @staticmethod
    def update(opportunity_id, data, user, active_role):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        if not AuthorizationService.can_edit_solution_design(user, active_role, opportunity):
            raise AuthorizationDenied("Only an assigned Solution Engineer can edit technical design.")
        design = opportunity.solution_design
        server_timestamp = design.updated_at if design is not None else opportunity.updated_at
        if ConcurrencyManager.has_conflict(data.get("updated_at"), server_timestamp):
            raise RuntimeError("Technical design changed since you opened it. Refresh before editing.")
        payload = {k: v for k, v in data.items() if k != "updated_at"}
        created = False
        if design is None:
            design = SolutionDesign(opportunity_id=opportunity.opportunity_id, **payload)
            db.session.add(design)
            created = True
        else:
            for key, value in payload.items():
                setattr(design, key, value)
        ActivityService.log(
            "Opportunity", opportunity.opportunity_id,
            SOLUTION_DESIGN_CREATED if created else SOLUTION_DESIGN_UPDATED,
            "Technical solution design created." if created else "Technical solution design updated.",
            user.user_id, commit=False,
        )
        db.session.commit()
        return design
