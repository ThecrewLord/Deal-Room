from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.repositories.stakeholder_repository import StakeholderRepository
from app.services.activity_service import ActivityService
from app.constants.activity_types import (
    STAKEHOLDER_CREATED,
    STAKEHOLDER_UPDATED,
)
from app.database import db
from app.models.opportunity.stakeholder import STAKEHOLDER_TAGS


class StakeholderService:

    @staticmethod
    def create_stakeholder(data, user, active_role):
        opportunity = StakeholderRepository.get_opportunity(
            data["opportunity_id"]
        )

        if not AuthorizationService.can_mutate_related(
            user,
            active_role,
            opportunity,
            "stakeholder",
            "create",
        ):
            raise AuthorizationDenied(
                "You are not authorized to create stakeholders for this opportunity."
            )

        stakeholder = StakeholderRepository.create(data)

        ActivityService.log(
            "Stakeholder",
            stakeholder.stakeholder_id,
            STAKEHOLDER_CREATED,
            f"Stakeholder '{stakeholder.stakeholder_name}' created.",
            user.user_id,
            commit=False,
        )

        db.session.commit()
        return stakeholder

    @staticmethod
    def get_by_id(stakeholder_id, user, active_role):
        stakeholder = StakeholderRepository.get_by_id(stakeholder_id)

        if not stakeholder:
            return None

        if not AuthorizationService.can_view_stakeholder(
            user,
            active_role,
            stakeholder,
        ):
            return None

        return stakeholder

    @staticmethod
    def get_by_opportunity(opportunity_id, user, active_role):
        opportunity = StakeholderRepository.get_opportunity(
            opportunity_id
        )

        if not AuthorizationService.can_view_opportunity(
            user,
            active_role,
            opportunity,
        ):
            return []

        return StakeholderRepository.get_by_opportunity(
            opportunity_id
        )

    @staticmethod
    def update_stakeholder(
        stakeholder_id,
        data,
        user,
        active_role,
    ):
        stakeholder = StakeholderRepository.get_by_id(
            stakeholder_id
        )

        if not stakeholder:
            return None

        if not AuthorizationService.can_mutate_related(
            user,
            active_role,
            stakeholder.opportunity,
            "stakeholder",
            "update",
        ):
            raise AuthorizationDenied(
                "You are not authorized to update this stakeholder."
            )

        incoming_updated_at = data.pop("updated_at", None)

        if incoming_updated_at and stakeholder.updated_at:
            if (
                incoming_updated_at.replace(tzinfo=None)
                != stakeholder.updated_at.replace(tzinfo=None)
            ):
                raise RuntimeError(
                    "This stakeholder was updated by someone else. "
                    "Please reload and try again."
                )

        updated = StakeholderRepository.update(
            stakeholder,
            data,
        )

        ActivityService.log(
            "Stakeholder",
            stakeholder.stakeholder_id,
            STAKEHOLDER_UPDATED,
            f"Stakeholder '{stakeholder.stakeholder_name}' updated.",
            user.user_id,
            commit=False,
        )

        db.session.commit()
        return updated

    @staticmethod
    def delete_stakeholder(
        stakeholder_id,
        user,
        active_role,
    ):
        stakeholder = StakeholderRepository.get_by_id(
            stakeholder_id
        )

        if not stakeholder:
            return False

        if not AuthorizationService.can_mutate_related(
            user,
            active_role,
            stakeholder.opportunity,
            "stakeholder",
            "delete",
        ):
            raise AuthorizationDenied(
                "You are not authorized to delete this stakeholder."
            )

        return StakeholderRepository.delete(stakeholder)

    # ---------------------------------------------------------
    # B2 — STAKEHOLDER TAGGING
    # ---------------------------------------------------------

    @staticmethod
    def add_tag(
        stakeholder_id,
        tag,
        user,
        active_role,
    ):
        """
        Add a tag to a stakeholder.

        Business rules:
        1. Tag must be one of the five supported tags.
        2. User must have permission to update the stakeholder.
        3. opportunity_id is ALWAYS taken from the stakeholder.
        4. A stakeholder cannot receive the same tag twice.
        5. Database prevents more than one Decision Maker
           per opportunity.
        """

        stakeholder = StakeholderRepository.get_by_id(
            stakeholder_id
        )

        if not stakeholder:
            return None

        if not AuthorizationService.can_mutate_related(
            user,
            active_role,
            stakeholder.opportunity,
            "stakeholder",
            "update",
        ):
            raise AuthorizationDenied(
                "You are not authorized to update this stakeholder."
            )

        if tag not in STAKEHOLDER_TAGS:
            raise ValueError(
                f"Invalid stakeholder tag. Allowed tags: "
                f"{', '.join(STAKEHOLDER_TAGS)}"
            )

        # IMPORTANT:
        # Never accept opportunity_id from the request.
        # It comes directly from the stakeholder.
        opportunity_id = stakeholder.opportunity_id

        # Prevent duplicate tag on the same stakeholder.
        existing_tags = StakeholderRepository.get_tags(
            stakeholder_id
        )

        if any(existing.tag == tag for existing in existing_tags):
            raise ValueError(
                f"Stakeholder already has the '{tag}' tag."
            )

        stakeholder_tag = StakeholderRepository.create_tag(
            stakeholder_id=stakeholder_id,
            opportunity_id=opportunity_id,
            tag=tag,
        )

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return stakeholder_tag

    @staticmethod
    def remove_tag(
        stakeholder_tag_id,
        user,
        active_role,
    ):
        """
        Remove a stakeholder tag after authorization.
        """

        stakeholder_tag = StakeholderRepository.get_tag_by_id(
            stakeholder_tag_id
        )

        if not stakeholder_tag:
            return None

        stakeholder = stakeholder_tag.stakeholder

        if not AuthorizationService.can_mutate_related(
            user,
            active_role,
            stakeholder.opportunity,
            "stakeholder",
            "update",
        ):
            raise AuthorizationDenied(
                "You are not authorized to update this stakeholder."
            )

        StakeholderRepository.delete_tag(
            stakeholder_tag
        )

        return True

    @staticmethod
    def get_tags(
        stakeholder_id,
        user,
        active_role,
    ):
        """
        Return all tags for a stakeholder after authorization.
        """

        stakeholder = StakeholderRepository.get_by_id(
            stakeholder_id
        )

        if not stakeholder:
            return None

        if not AuthorizationService.can_view_stakeholder(
            user,
            active_role,
            stakeholder,
        ):
            return []

        return StakeholderRepository.get_tags(
            stakeholder_id
        )

    @staticmethod
    def get_decision_maker(
        opportunity_id,
        user,
        active_role,
    ):
        """
        Return the Decision Maker for an opportunity, if one exists.
        """

        opportunity = StakeholderRepository.get_opportunity(
            opportunity_id
        )

        if not AuthorizationService.can_view_opportunity(
            user,
            active_role,
            opportunity,
        ):
            return None

        return StakeholderRepository.get_decision_maker(
            opportunity_id
        )