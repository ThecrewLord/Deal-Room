from app.constants.auth_constants import STATUS_APPROVED
from app.constants.activity_types import (
    DELIVERY_ASSIGNMENT_CREATED,
    DELIVERY_ASSIGNMENT_REACTIVATED,
    DELIVERY_ASSIGNMENT_REMOVED,
)
from app.constants.roles import (
    DATA_ANALYST,
    DELIVERY,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
)

from app.database import db

from app.models.auth.user import User
from app.models.delivery.delivery_project import DeliveryProject

from app.repositories.delivery_assignment_repository import (
    DeliveryAssignmentRepository,
)

from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService


class DeliveryAssignmentService:

    VALID_ROLES = {
        DELIVERY_MANAGER,
        DEVOPS_ENGINEER,
        DATA_ANALYST,
        DELIVERY,
    }

    # ================================================================
    # ASSIGN
    # ================================================================

    @staticmethod
    def assign(
        project_id,
        user_id,
        role,
        assigned_by,
        active_role,
    ):
        # ------------------------------------------------------------
        # Validate project
        # ------------------------------------------------------------

        project = db.session.get(
            DeliveryProject,
            project_id,
        )

        if not project:
            raise ValueError(
                "Delivery project not found."
            )

        # ------------------------------------------------------------
        # Only Delivery Manager can assign team members.
        # ------------------------------------------------------------

        if active_role != DELIVERY_MANAGER:
            raise ValueError(
                "Only a Delivery Manager can assign "
                "delivery team members."
            )

        # ------------------------------------------------------------
        # Validate assigning user
        # ------------------------------------------------------------

        assigning_user = db.session.get(
            User,
            assigned_by,
        )

        if not assigning_user:
            raise ValueError(
                "Assigning user not found."
            )

        if not assigning_user.active:
            raise ValueError(
                "Assigning user is inactive."
            )

        if assigning_user.status != STATUS_APPROVED:
            raise ValueError(
                "Assigning user is not approved."
            )

        if not assigning_user.has_role(
            DELIVERY_MANAGER
        ):
            raise ValueError(
                "Assigning user is not a Delivery Manager."
            )

        # ------------------------------------------------------------
        # Completed projects cannot be modified.
        # ------------------------------------------------------------

        if project.status == "Done":
            raise ValueError(
                "Cannot modify assignments on a completed project."
            )

        # ------------------------------------------------------------
        # Validate requested role.
        # ------------------------------------------------------------

        if role not in DeliveryAssignmentService.VALID_ROLES:
            raise ValueError(
                "Invalid delivery role."
            )

        # ------------------------------------------------------------
        # Validate target user.
        # ------------------------------------------------------------

        target_user = db.session.get(
            User,
            user_id,
        )

        if not target_user:
            raise ValueError(
                "Target user not found."
            )

        if not target_user.active:
            raise ValueError(
                "Cannot assign an inactive user."
            )

        if target_user.status != STATUS_APPROVED:
            raise ValueError(
                "Cannot assign an unapproved user."
            )

        # ------------------------------------------------------------
        # User must actually have the requested role.
        # ------------------------------------------------------------

        if not target_user.has_role(role):
            raise ValueError(
                f"User does not have the {role} role."
            )

        # ------------------------------------------------------------
        # Check previous assignment.
        # ------------------------------------------------------------

        existing = (
            DeliveryAssignmentRepository
            .get_by_project_and_user(
                project_id,
                user_id,
            )
        )

        # ------------------------------------------------------------
        # Already actively assigned.
        # ------------------------------------------------------------

        if existing and existing.is_active:
            raise ValueError(
                "User is already assigned to this project."
            )

        # ------------------------------------------------------------
        # Reactivate previous assignment.
        # ------------------------------------------------------------

        if existing:

            existing.is_active = True
            existing.role = role
            existing.assigned_by = assigned_by

            ActivityService.log(
                entity_type="delivery_project",
                entity_id=project.project_id,
                action=DELIVERY_ASSIGNMENT_REACTIVATED,
                description=(
                    f"{target_user.full_name} was reassigned "
                    f"to project '{project.project_name}' "
                    f"as {role}."
                ),
                user_id=assigned_by,
                commit=False,
            )

            NotificationService.queue(
                target_user.user_id,
                "DELIVERY_PROJECT_ASSIGNED",
                "delivery_project",
                project.project_id,
                (
                    f"You have been reassigned to delivery project "
                    f"'{project.project_name}' as {role}."
                ),
            )

            db.session.commit()

            return existing

        # ------------------------------------------------------------
        # Create new assignment.
        # ------------------------------------------------------------

        assignment = (
            DeliveryAssignmentRepository.create(
                {
                    "project_id": project_id,
                    "user_id": user_id,
                    "assigned_by": assigned_by,
                    "role": role,
                    "is_active": True,
                }
            )
        )

        # ------------------------------------------------------------
        # Audit activity.
        # ------------------------------------------------------------

        ActivityService.log(
            entity_type="delivery_project",
            entity_id=project.project_id,
            action=DELIVERY_ASSIGNMENT_CREATED,
            description=(
                f"{target_user.full_name} was assigned "
                f"to project '{project.project_name}' "
                f"as {role}."
            ),
            user_id=assigned_by,
            commit=False,
        )

        NotificationService.queue(
            target_user.user_id,
            "DELIVERY_PROJECT_ASSIGNED",
            "delivery_project",
            project.project_id,
            (
                f"You have been assigned to delivery project "
                f"'{project.project_name}' as {role}."
            ),
        )

        # ------------------------------------------------------------
        # Commit assignment + audit + notification together.
        # ------------------------------------------------------------

        db.session.commit()

        return assignment

    # ================================================================
    # GET ASSIGNMENTS
    # ================================================================

    @staticmethod
    def get_assignments(
        project_id,
    ):
        project = db.session.get(
            DeliveryProject,
            project_id,
        )

        if not project:
            raise ValueError(
                "Delivery project not found."
            )

        return (
            DeliveryAssignmentRepository
            .get_active_by_project(
                project_id
            )
        )

    # ================================================================
    # REMOVE ASSIGNMENT
    # ================================================================


    @staticmethod
    def get_candidates():
        """
        Return active and approved users who can be assigned
        to a delivery project.

        Delivery Manager is intentionally excluded because the
        Delivery Manager performs the assignment rather than
        being a normal project-team candidate.
        """

        candidates = (
            User.query
            .filter(
                User.active.is_(True),
                User.status == STATUS_APPROVED,
            )
            .order_by(User.full_name.asc())
            .all()
        )

        result = []

        for user in candidates:
            roles = [
                role.role
                for role in user.roles
                if role.role in {
                    DEVOPS_ENGINEER,
                    DATA_ANALYST,
                    DELIVERY,
                }
            ]

            if not roles:
                continue

            result.append({
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "roles": sorted(set(roles)),
            })

        return result

    @staticmethod
    def remove_assignment(
        project_id,
        user_id,
        removed_by,
        active_role,
    ):
        # ------------------------------------------------------------
        # Validate project.
        # ------------------------------------------------------------

        project = db.session.get(
            DeliveryProject,
            project_id,
        )

        if not project:
            raise ValueError(
                "Delivery project not found."
            )

        # ------------------------------------------------------------
        # Only Delivery Manager can remove assignments.
        # ------------------------------------------------------------

        if active_role != DELIVERY_MANAGER:
            raise ValueError(
                "Only a Delivery Manager can remove "
                "delivery team assignments."
            )

        # ------------------------------------------------------------
        # Validate removing user.
        # ------------------------------------------------------------

        removing_user = db.session.get(
            User,
            removed_by,
        )

        if not removing_user:
            raise ValueError(
                "Removing user not found."
            )

        if not removing_user.active:
            raise ValueError(
                "Removing user is inactive."
            )

        if removing_user.status != STATUS_APPROVED:
            raise ValueError(
                "Removing user is not approved."
            )

        if not removing_user.has_role(
            DELIVERY_MANAGER
        ):
            raise ValueError(
                "Removing user is not a Delivery Manager."
            )

        # ------------------------------------------------------------
        # Completed projects cannot be modified.
        # ------------------------------------------------------------

        if project.status == "Done":
            raise ValueError(
                "Cannot modify assignments on a completed project."
            )

        # ------------------------------------------------------------
        # Find assignment.
        # ------------------------------------------------------------

        assignment = (
            DeliveryAssignmentRepository
            .get_by_project_and_user(
                project_id,
                user_id,
            )
        )

        if not assignment:
            raise ValueError(
                "User is not assigned to this project."
            )

        if not assignment.is_active:
            raise ValueError(
                "User is already removed from this project."
            )

        # ------------------------------------------------------------
        # Deactivate assignment.
        # ------------------------------------------------------------

        DeliveryAssignmentRepository.deactivate(
            assignment
        )

        # ------------------------------------------------------------
        # Audit activity.
        # ------------------------------------------------------------

        target_user = db.session.get(
            User,
            user_id,
        )

        target_name = (
            target_user.full_name
            if target_user
            else f"user {user_id}"
        )

        ActivityService.log(
            entity_type="delivery_project",
            entity_id=project.project_id,
            action=DELIVERY_ASSIGNMENT_REMOVED,
            description=(
                f"{target_name} was removed from "
                f"project '{project.project_name}'."
            ),
            user_id=removed_by,
            commit=False,
        )

        # ------------------------------------------------------------
        # Commit assignment removal + audit.
        # ------------------------------------------------------------

        db.session.commit()

        return assignment