from datetime import date, datetime

from app.auth.authorization import AuthorizationService
from app.database import db

from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker

from app.repositories.delivery_project_repository import (
    DeliveryProjectRepository,
)

from app.repositories.delivery_assignment_repository import (
    DeliveryAssignmentRepository,
)

from app.services.activity_service import ActivityService


class DeliveryProjectService:

    @staticmethod
    def _parse_date(value, field_name):
        """
        Convert an ISO date string (YYYY-MM-DD) into a Python date.
        Accept an existing date object as-is.
        """
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return datetime.strptime(
                    value,
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                raise ValueError(
                    f"{field_name} must be in YYYY-MM-DD format."
                )

        raise ValueError(
            f"{field_name} must be in YYYY-MM-DD format."
        )

    @staticmethod
    def transition_status(
        project_id,
        new_status,
        user_id,
        active_role,
    ):
        """
        Move a delivery project through its controlled lifecycle.

        Pending Assignment -> Assigned
        Assigned -> In Progress
        In Progress -> Done
        """

        from app.constants.roles import (
            DELIVERY_MANAGER,
            DEVOPS_ENGINEER,
            DATA_ANALYST,
            DELIVERY,
        )

        project = DeliveryProjectRepository.get_by_id(project_id)

        if not project:
            raise ValueError("Delivery project not found.")

        allowed_transitions = {
            "Pending Assignment": {"Assigned"},
            "Assigned": {"In Progress"},
            "In Progress": {"Done"},
            "Done": set(),
        }

        current_status = project.status

        if new_status not in allowed_transitions.get(
            current_status,
            set(),
        ):
            raise ValueError(
                f"Invalid project status transition: "
                f"{current_status} -> {new_status}."
            )

        actor = db.session.get(User, user_id)

        if not actor:
            raise ValueError("User not found.")

        if not actor.active:
            raise ValueError("Inactive users cannot change project status.")

        from app.constants.auth_constants import STATUS_APPROVED

        if actor.status != STATUS_APPROVED:
            raise ValueError("Unapproved users cannot change project status.")

        active_assignments = DeliveryAssignmentRepository.get_active_by_project(
            project_id
        )

        # ------------------------------------------------------------
        # Pending Assignment -> Assigned
        # Only Delivery Manager can finalize assignment.
        # At least one active delivery assignment is required.
        # ------------------------------------------------------------

        if current_status == "Pending Assignment":
            if active_role != DELIVERY_MANAGER:
                raise ValueError(
                    "Only a Delivery Manager can assign a delivery project."
                )

            if not active_assignments:
                raise ValueError(
                    "At least one delivery team member must be assigned "
                    "before the project can be marked Assigned."
                )

        # ------------------------------------------------------------
        # Assigned -> In Progress
        # Only an actively assigned project member can start execution.
        # ------------------------------------------------------------

        elif current_status == "Assigned":
            if active_role == DELIVERY_MANAGER:
                pass
            elif active_role in {
                DEVOPS_ENGINEER,
                DATA_ANALYST,
                DELIVERY,
            }:
                authorized = any(
                    assignment.user_id == user_id
                    and assignment.is_active
                    and assignment.role == active_role
                    for assignment in active_assignments
                )

                if not authorized:
                    raise ValueError(
                        "Only an assigned delivery team member can "
                        "start this project."
                    )
            else:
                raise ValueError(
                    "Only the Delivery Manager or an assigned "
                    "delivery team member can start this project."
                )

        # ------------------------------------------------------------
        # In Progress -> Done
        # Only Delivery Manager or assigned team member.
        # ------------------------------------------------------------

        elif current_status == "In Progress":
            if active_role == DELIVERY_MANAGER:
                pass
            elif active_role in {
                DEVOPS_ENGINEER,
                DATA_ANALYST,
                DELIVERY,
            }:
                authorized = any(
                    assignment.user_id == user_id
                    and assignment.is_active
                    and assignment.role == active_role
                    for assignment in active_assignments
                )

                if not authorized:
                    raise ValueError(
                        "Only an assigned delivery team member can "
                        "complete this project."
                    )
            else:
                raise ValueError(
                    "Only the Delivery Manager or an assigned "
                    "delivery team member can complete this project."
                )

        project.status = new_status

        action_map = {
            "Assigned": "DELIVERY_PROJECT_STARTED",
            "In Progress": "DELIVERY_PROJECT_STARTED",
            "Done": "DELIVERY_PROJECT_COMPLETED",
        }

        action = action_map[new_status]

        ActivityService.log(
            entity_type="delivery_project",
            entity_id=project.project_id,
            action=action,
            description=(
                f"Delivery project '{project.project_name}' "
                f"status changed from '{current_status}' "
                f"to '{new_status}'."
            ),
            user_id=user_id,
            commit=False,
        )

        db.session.commit()

        return project

    @staticmethod
    def create_project(
        opportunity_id,
        poc_id,
        project_name,
        created_by,
        active_role,
        start_date=None,
        target_date=None,
    ):
        # ------------------------------------------------------------
        # Validate opportunity
        # ------------------------------------------------------------

        opportunity = db.session.get(
            Opportunity,
            opportunity_id,
        )

        if not opportunity:
            raise ValueError(
                "Opportunity not found."
            )

        # ------------------------------------------------------------
        # Validate POC
        # ------------------------------------------------------------

        poc = db.session.get(
            POCTracker,
            poc_id,
        )

        if not poc:
            raise ValueError(
                "POC not found."
            )

        # ------------------------------------------------------------
        # POC must belong to the opportunity
        # ------------------------------------------------------------

        if poc.opportunity_id != opportunity_id:
            raise ValueError(
                "POC does not belong to this opportunity."
            )

        # ------------------------------------------------------------
        # Validate project name
        # ------------------------------------------------------------

        if not project_name:
            raise ValueError(
                "project_name is required."
            )

        project_name = project_name.strip()

        if not project_name:
            raise ValueError(
                "project_name is required."
            )

        # ------------------------------------------------------------
        # Validate creating user
        # ------------------------------------------------------------

        creator = db.session.get(
            User,
            created_by,
        )

        if not creator:
            raise ValueError(
                "Creating user not found."
            )

        # ------------------------------------------------------------
        # Authorization
        #
        # Only:
        #   Approved + Active Delivery Manager
        #
        # can create a project from:
        #   Completed POC
        # ------------------------------------------------------------

        if not AuthorizationService.can_create_delivery_project(
            creator,
            active_role,
            opportunity,
            poc,
        ):
            raise ValueError(
                "Only a Delivery Manager can create "
                "a project from a completed POC."
            )

        # ------------------------------------------------------------
        # Parse dates
        # ------------------------------------------------------------

        start_date = DeliveryProjectService._parse_date(
            start_date,
            "start_date",
        )

        target_date = DeliveryProjectService._parse_date(
            target_date,
            "target_date",
        )

        # ------------------------------------------------------------
        # Validate date relationship
        # ------------------------------------------------------------

        if (
            start_date
            and target_date
            and target_date < start_date
        ):
            raise ValueError(
                "target_date cannot be before start_date."
            )

        # ------------------------------------------------------------
        # One delivery project per POC
        # ------------------------------------------------------------

        existing_projects = (
            DeliveryProjectRepository.get_by_poc(
                poc_id
            )
        )

        if existing_projects:
            raise ValueError(
                "A delivery project already exists for this POC."
            )

        # ------------------------------------------------------------
        # Create project
        # ------------------------------------------------------------

        project = DeliveryProjectRepository.create(
            {
                "opportunity_id": opportunity_id,
                "poc_id": poc_id,
                "project_name": project_name,
                "status": "Pending Assignment",
                "start_date": start_date,
                "target_date": target_date,
                "created_by": created_by,
            }
        )

        # ------------------------------------------------------------
        # Audit activity
        # ------------------------------------------------------------

        ActivityService.log(
            entity_type="delivery_project",
            entity_id=project.project_id,
            action="DELIVERY_PROJECT_CREATED",
            description=(
                f"Delivery project '{project.project_name}' "
                f"created for opportunity {opportunity_id} "
                f"from completed POC {poc_id}."
            ),
            user_id=created_by,
            commit=False,
        )

        # ------------------------------------------------------------
        # Commit project + audit together
        # ------------------------------------------------------------

        db.session.commit()

        return project