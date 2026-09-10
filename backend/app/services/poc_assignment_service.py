from app.database import db
from app.models.auth import User
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.constants.roles import PRE_SALES_MANAGER, SOLUTION_ENGINEER
from app.auth.authorization import AuthorizationService
from app.repositories.poc_assignment_repository import PocAssignmentRepository
from app.services.activity_service import ActivityService


class PocAssignmentService:

    @staticmethod
    def assign(poc_id, user_id, assigned_by, active_role):

        # 1. POC must exist
        poc = db.session.get(POCTracker, poc_id)
        if not poc:
            raise ValueError("POC not found.")

        # 2. Only a Pre-Sales Manager can assign a POC.
        assigning_user = db.session.get(User, assigned_by)

        if not AuthorizationService.can_assign_poc(
            assigning_user,
            active_role,
            poc,
        ):
            raise ValueError(
                "Only a Pre-Sales Manager can assign a POC."
            )

        # 3. User must exist
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        # 4. User must be active and approved
        if not user.active:
            raise ValueError("User is inactive.")

        if user.status != "APPROVED":
            raise ValueError("User is not approved.")

        # 5. User must be a Solution Engineer
        has_se_role = any(
            role.role == SOLUTION_ENGINEER
            for role in user.roles
        )

        if not has_se_role:
            raise ValueError(
                "POC can only be assigned to a Solution Engineer."
            )

        # 6. User must belong to the opportunity technical team
        team_member = (
            OpportunityTeam.query
            .filter_by(
                opportunity_id=poc.opportunity_id,
                user_id=user_id,
                role=SOLUTION_ENGINEER,
            )
            .first()
        )

        if not team_member:
            raise ValueError(
                "User is not assigned to the opportunity as a Solution Engineer."
            )

        # 7. Prevent duplicate active assignment
        existing = (
            PocAssignmentRepository
            .get_by_poc_and_user(poc_id, user_id)
        )

        if existing:
            if existing.is_active:
                raise ValueError(
                    "User is already assigned to this POC."
                )

            # Reactivate previous assignment
            existing.is_active = True
            existing.assigned_by = assigned_by

            ActivityService.log(
                "POC",
                poc_id,
                "POC_ASSIGNED",
                f"POC reassigned to user {user_id}.",
                assigned_by,
                commit=False,
            )

            db.session.commit()
            return existing

        # 8. Create assignment
        assignment = PocAssignmentRepository.create(
            {
                "poc_id": poc_id,
                "user_id": user_id,
                "assigned_by": assigned_by,
                "role": SOLUTION_ENGINEER,
                "is_active": True,
            }
        )

        # 9. Audit history
        ActivityService.log(
            "POC",
            poc_id,
            "POC_ASSIGNED",
            f"POC assigned to user {user_id}.",
            assigned_by,
            commit=False,
        )

        db.session.commit()

        return assignment

    @staticmethod
    def get_assignments(poc_id):
        return PocAssignmentRepository.get_active_by_poc(poc_id)

    @staticmethod
    def remove_assignment(poc_id, user_id, removed_by, active_role):

        poc = db.session.get(POCTracker, poc_id)

        if not poc:
            raise ValueError("POC not found.")

        removing_user = db.session.get(User, removed_by)

        if not AuthorizationService.can_assign_poc(
            removing_user,
            active_role,
            poc,
        ):
            raise ValueError(
                "Only a Pre-Sales Manager can remove a POC assignment."
            )

        assignment = (
            PocAssignmentRepository
            .get_by_poc_and_user(poc_id, user_id)
        )

        if not assignment or not assignment.is_active:
            raise ValueError("Active POC assignment not found.")

        assignment.is_active = False

        ActivityService.log(
            "POC",
            poc_id,
            "POC_ASSIGNMENT_REMOVED",
            f"POC assignment removed for user {user_id}.",
            removed_by,
            commit=False,
        )

        db.session.commit()

        return assignment
