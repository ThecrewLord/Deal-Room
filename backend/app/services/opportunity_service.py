from datetime import datetime

from sqlalchemy.exc import IntegrityError, OperationalError

from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.activity_types import (
    OPPORTUNITY_APPROVED,
    OPPORTUNITY_QUALIFIED,
    OPPORTUNITY_REJECTED,
    OPPORTUNITY_SUBMITTED_FOR_REVIEW,
    SALES_OWNER_ASSIGNED,
    OPPORTUNITY_SENT_TO_PRE_SALES,
    PRE_SALES_ASSIGNMENT_FINALIZED,
    OPPORTUNITY_STAGE_CHANGED,
    SOLUTION_ENGINEER_ASSIGNED,
    DELIVERY_ASSIGNED,
)
from app.constants.auth_constants import STATUS_APPROVED
from app.constants.roles import PRE_SALES_MANAGER, SALES_EXECUTIVE, SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY
from app.constants.stages import (
    ACTIVE_STATUS,
    APPROVED_STATUS,
    INITIAL_STAGE_NAME,
    OPEN_STATUS,
    PENDING_SALES_MANAGER_REVIEW_STATUS,
    QUALIFICATION_STAGE_NAME,
    REJECTED_STATUS,
)
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService
from app.services.stage_service import StageService
from app.repositories.stage_repository import StageRepository
from app.utils.concurrency import ConcurrencyManager


class OpportunityService:

    @staticmethod
    def create_opportunity(data, user, active_role):
        if not AuthorizationService.can_create_opportunity(user, active_role):
            raise AuthorizationDenied("You are not authorized to create opportunities.")

        account = Account.query.filter_by(account_id=data["account_id"]).first()
        if not AuthorizationService.can_view_account(user, active_role, account):
            raise AuthorizationDenied(
                "You are not authorized to create an opportunity for this account."
            )

        if OpportunityRepository.exists(data["opportunity_name"], data["account_id"]):
            raise ValueError("Opportunity already exists for this account.")

        initial_stage = StageService.get_initial_stage()
        if not initial_stage:
            raise RuntimeError(f"Required stage '{INITIAL_STAGE_NAME}' is not configured.")

        opportunity = Opportunity(
            account_id=data["account_id"],
            created_by=user.user_id,
            sales_owner_id=None,
            stage_id=initial_stage.stage_id,
            opportunity_name=data["opportunity_name"],
            description=data.get("description"),
            estimated_value=data.get("estimated_value", 0),
            probability=data.get("probability", 0),
            expected_close_date=data.get("expected_close_date"),
            status=OPEN_STATUS,
            is_active=True,
        )

        db.session.add(opportunity)
        db.session.flush()
        db.session.add(OpportunityTeam(
            opportunity_id=opportunity.opportunity_id,
            user_id=user.user_id,
            role=active_role,
        ))
        StageService.record_initial_stage(opportunity, user.user_id)
        ActivityService.log(
            entity_type="Opportunity",
            entity_id=opportunity.opportunity_id,
            action="CREATE_OPPORTUNITY",
            description=f"Opportunity '{opportunity.opportunity_name}' created.",
            user_id=user.user_id,
            commit=False,
        )
        db.session.commit()
        return opportunity

    @staticmethod
    def get_all(user, active_role):
        return OpportunityRepository.get_all(
            AuthorizationService.opportunity_query(user, active_role)
        )

    @staticmethod
    def get_pending_review(user, active_role):
        if not AuthorizationService.can_view_pending_review(user, active_role):
            raise AuthorizationDenied("Only a Sales Manager can view the review queue.")
        return OpportunityRepository.get_pending_sales_manager_review(
            AuthorizationService.opportunity_query(user, active_role)
        )

    @staticmethod
    def get_eligible_sales_owners(user, active_role):
        if not AuthorizationService.can_view_pending_review(user, active_role):
            raise AuthorizationDenied("Only a Sales Manager can view Sales Owner candidates.")
        return OpportunityRepository.get_eligible_sales_owners()

    @staticmethod
    def get_pending_pre_sales_assignment(user, active_role):
        if not AuthorizationService.can_view_pending_pre_sales_assignment(user, active_role):
            raise AuthorizationDenied("Only a Pre-Sales Manager can view the pending assignment queue.")
        return OpportunityRepository.get_pending_pre_sales_assignment()

    @staticmethod
    def get_eligible_pre_sales_users(user, active_role, role):
        if not AuthorizationService.can_view_pending_pre_sales_assignment(
            user, active_role
        ):
            raise AuthorizationDenied(
                "Only a Pre-Sales Manager can view technical assignment candidates."
            )

        if role not in {SOLUTION_ENGINEER, DELIVERY}:
            raise ValueError(
                "Assignment role must be Solution Engineer or Delivery."
            )

        return OpportunityRepository.get_eligible_users(role)

    @staticmethod
    def finalize_pre_sales_assignment(
        opportunity_id,
        solution_engineer_ids,
        delivery_ids=None,
        updated_at=None,
        user=None,
        active_role=None,
    ):
        if active_role != PRE_SALES_MANAGER:
            raise AuthorizationDenied(
                "Only the active Pre-Sales Manager role can finalize technical assignment."
            )

        opportunity = OpportunityRepository.get_by_id(opportunity_id)

        if not opportunity:
            return None

        if not AuthorizationService.can_view_opportunity(
            user, active_role, opportunity
        ):
            return None

        if OpportunityTeam.query.filter(
            OpportunityTeam.opportunity_id == opportunity.opportunity_id,
            OpportunityTeam.role == SOLUTION_ENGINEER,
        ).first():
            raise RuntimeError(
                "Technical assignment has already been finalized."
            )

        if not AuthorizationService.can_finalize_pre_sales_assignment(
            user, active_role, opportunity
        ):
            raise RuntimeError(
                "Opportunity is not awaiting Pre-Sales assignment."
            )

        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(
                updated_at.replace("Z", "+00:00")
            )

        if ConcurrencyManager.has_conflict(
            updated_at, opportunity.updated_at
        ):
            raise RuntimeError(
                "This opportunity has changed since you opened it. "
                "Refresh before assigning the technical team."
            )

        # --------------------------------------------------------
        # Keep the two assignment groups separate.
        # --------------------------------------------------------

        se_ids = [int(uid) for uid in (solution_engineer_ids or [])]
        delivery_member_ids = [int(uid) for uid in (delivery_ids or [])]

        if len(se_ids) != len(set(se_ids)):
            raise ValueError(
                "Duplicate Solution Engineer assignment is not allowed."
            )

        if len(delivery_member_ids) != len(set(delivery_member_ids)):
            raise ValueError(
                "Duplicate Delivery assignment is not allowed."
            )

        if not se_ids:
            raise ValueError(
                "At least one Solution Engineer is required."
            )

        if not delivery_member_ids:
            raise ValueError(
                "At least one Delivery member is required."
            )

        # A user cannot be assigned simultaneously to both groups.
        overlap = set(se_ids).intersection(delivery_member_ids)

        if overlap:
            raise ValueError(
                "A selected user cannot be assigned as both "
                "Solution Engineer and Delivery."
            )

        all_ids = se_ids + delivery_member_ids

        users = {
            u.user_id: u
            for u in User.query.filter(
                User.user_id.in_(all_ids)
            ).all()
        }

        if len(users) != len(all_ids):
            raise ValueError(
                "One or more selected users do not exist."
            )

        # --------------------------------------------------------
        # Validate Solution Engineers.
        # --------------------------------------------------------

        for uid in se_ids:
            candidate = users.get(uid)

            if (
                not candidate
                or not candidate.active
                or candidate.status != STATUS_APPROVED
                or not candidate.has_role(SOLUTION_ENGINEER)
            ):
                raise ValueError(
                    f"User {uid} is not an eligible Solution Engineer."
                )

        # --------------------------------------------------------
        # Validate Delivery members.
        # --------------------------------------------------------

        for uid in delivery_member_ids:
            candidate = users.get(uid)

            if (
                not candidate
                or not candidate.active
                or candidate.status != STATUS_APPROVED
                or not candidate.has_role(DELIVERY)
            ):
                raise ValueError(
                    f"User {uid} is not an eligible Delivery member."
                )

        # --------------------------------------------------------
        # Prevent duplicate opportunity assignments.
        # --------------------------------------------------------

        existing_ids = {
            row.user_id
            for row in OpportunityTeam.query.filter_by(
                opportunity_id=opportunity.opportunity_id
            ).all()
        }

        if existing_ids.intersection(all_ids):
            raise ValueError(
                "A selected user is already assigned to this opportunity."
            )

        # --------------------------------------------------------
        # Approved -> Active is part of the existing Phase 5 flow.
        # --------------------------------------------------------

        updated_rows = Opportunity.query.filter(
            Opportunity.opportunity_id == opportunity.opportunity_id,
            Opportunity.status == APPROVED_STATUS,
            Opportunity.sales_owner_id.isnot(None),
            Opportunity.is_active.is_(True),
        ).update(
            {"status": ACTIVE_STATUS},
            synchronize_session=False,
        )

        if updated_rows != 1:
            db.session.rollback()
            raise RuntimeError(
                "Technical assignment has already been finalized or "
                "the opportunity is no longer assignable."
            )

        db.session.expire(
            opportunity,
            ["status", "updated_at"],
        )
        db.session.refresh(opportunity)

        try:
            # ----------------------------------------------------
            # Create Solution Engineer assignments.
            # ----------------------------------------------------

            for uid in se_ids:
                db.session.add(
                    OpportunityTeam(
                        opportunity_id=opportunity.opportunity_id,
                        user_id=uid,
                        role=SOLUTION_ENGINEER,
                    )
                )

            # ----------------------------------------------------
            # Create Delivery assignments.
            # ----------------------------------------------------

            for uid in delivery_member_ids:
                db.session.add(
                    OpportunityTeam(
                        opportunity_id=opportunity.opportunity_id,
                        user_id=uid,
                        role=DELIVERY,
                    )
                )

            # ----------------------------------------------------
            # Finalization audit.
            # ----------------------------------------------------

            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action=PRE_SALES_ASSIGNMENT_FINALIZED,
                description=(
                    "Technical team assigned. "
                    f"Solution Engineers: "
                    f"{', '.join(users[uid].full_name for uid in se_ids)}. "
                    f"Delivery: "
                    f"{', '.join(users[uid].full_name for uid in delivery_member_ids)}."
                ),
                user_id=user.user_id,
                commit=False,
            )

            # ----------------------------------------------------
            # Solution Engineer audit + notification.
            # ----------------------------------------------------

            for uid in se_ids:
                ActivityService.log(
                    entity_type="Opportunity",
                    entity_id=opportunity.opportunity_id,
                    action=SOLUTION_ENGINEER_ASSIGNED,
                    description=(
                        f"{users[uid].full_name} assigned "
                        "as Solution Engineer."
                    ),
                    user_id=user.user_id,
                    commit=False,
                )

                NotificationService.queue(
                    uid,
                    SOLUTION_ENGINEER_ASSIGNED,
                    "Opportunity",
                    opportunity.opportunity_id,
                    (
                        f"You have been assigned to Opportunity "
                        f"'{opportunity.opportunity_name}' "
                        "as Solution Engineer."
                    ),
                )

            # ----------------------------------------------------
            # Delivery audit + notification.
            # ----------------------------------------------------

            for uid in delivery_member_ids:
                ActivityService.log(
                    entity_type="Opportunity",
                    entity_id=opportunity.opportunity_id,
                    action=DELIVERY_ASSIGNED,
                    description=(
                        f"{users[uid].full_name} assigned "
                        "as Delivery."
                    ),
                    user_id=user.user_id,
                    commit=False,
                )

                NotificationService.queue(
                    uid,
                    DELIVERY_ASSIGNED,
                    "Opportunity",
                    opportunity.opportunity_id,
                    (
                        f"You have been assigned to Opportunity "
                        f"'{opportunity.opportunity_name}' "
                        "as Delivery."
                    ),
                )

            db.session.commit()
            return opportunity

        except (IntegrityError, OperationalError):
            db.session.rollback()
            raise RuntimeError(
                "Technical assignment could not be finalized because "
                "the opportunity was changed concurrently."
            )

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_id(opportunity_id, user, active_role):
        return OpportunityRepository.get_by_id(
            opportunity_id,
            AuthorizationService.opportunity_query(user, active_role),
        )

    @staticmethod
    def update_opportunity(opportunity_id, data, user, active_role):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None

        if not AuthorizationService.can_update_opportunity(user, active_role, opportunity, data):
            raise AuthorizationDenied("You are not authorized to update this opportunity.")

        client_timestamp = data.pop("updated_at", None)
        if isinstance(client_timestamp, str):
            client_timestamp = datetime.fromisoformat(client_timestamp.replace("Z", "+00:00"))
        if ConcurrencyManager.has_conflict(client_timestamp, opportunity.updated_at):
            raise RuntimeError(
                "This opportunity has been modified by another user. Please refresh and try again."
            )

        allowed_fields = {
            "opportunity_name",
            "description",
            "estimated_value",
            "probability",
            "expected_close_date",
        }
        for key, value in data.items():
            if key in allowed_fields:
                setattr(opportunity, key, value)

        ActivityService.log(
            entity_type="Opportunity",
            entity_id=opportunity.opportunity_id,
            action="UPDATE_OPPORTUNITY",
            description=f"Opportunity '{opportunity.opportunity_name}' updated.",
            user_id=user.user_id,
            commit=False,
        )
        db.session.commit()
        return opportunity

    @staticmethod
    def qualify_opportunity(opportunity_id, user, active_role):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        if not AuthorizationService.can_qualify_opportunity(user, active_role, opportunity):
            raise AuthorizationDenied("You are not authorized to qualify this opportunity.")

        qualification = StageRepository.get_by_name(QUALIFICATION_STAGE_NAME)
        if not qualification:
            raise RuntimeError("Required stage 'Qualification' is not configured.")

        opportunity.stage_id = qualification.stage_id
        opportunity.status = OPEN_STATUS
        opportunity.is_active = True
        from app.models.opportunity.stage_history import StageHistory
        db.session.add(StageHistory(
            opportunity_id=opportunity.opportunity_id,
            stage_id=qualification.stage_id,
            changed_by=user.user_id,
            remarks="Opportunity qualified by Sales Executive.",
        ))
        ActivityService.log(
            entity_type="Opportunity",
            entity_id=opportunity.opportunity_id,
            action=OPPORTUNITY_STAGE_CHANGED,
            description="Stage changed from 'Lead / Identified' to 'Qualification'.",
            user_id=user.user_id,
            commit=False,
        )
        ActivityService.log(
            entity_type="Opportunity",
            entity_id=opportunity.opportunity_id,
            action=OPPORTUNITY_QUALIFIED,
            description="Opportunity moved from Lead / Identified to Qualification.",
            user_id=user.user_id,
            commit=False,
        )
        db.session.commit()
        return opportunity

    @staticmethod
    def submit_for_sales_manager_review(opportunity_id, user, active_role):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        if not AuthorizationService.can_submit_for_review(user, active_role, opportunity):
            raise AuthorizationDenied(
                "Only the creating Sales Executive can submit a qualified opportunity for review."
            )

        opportunity.status = PENDING_SALES_MANAGER_REVIEW_STATUS
        opportunity.is_active = True

        ActivityService.log(
            entity_type="Opportunity",
            entity_id=opportunity.opportunity_id,
            action=OPPORTUNITY_SUBMITTED_FOR_REVIEW,
            description="Opportunity submitted for Sales Manager review.",
            user_id=user.user_id,
            commit=False,
        )

        managers = User.query.filter(
            User.active.is_(True),
            User.status == STATUS_APPROVED,
            User.roles.any(role=SALES_MANAGER),
        ).all()
        for manager in managers:
            NotificationService.queue(
                manager.user_id,
                OPPORTUNITY_SUBMITTED_FOR_REVIEW,
                "Opportunity",
                opportunity.opportunity_id,
                f"Opportunity '{opportunity.opportunity_name}' requires Sales Manager review.",
            )
        db.session.commit()
        return opportunity

    @staticmethod
    def review_opportunity(opportunity_id, decision, sales_owner_id, reason, updated_at, user, active_role):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None

        if not AuthorizationService.can_review_opportunity(user, active_role, opportunity):
            raise AuthorizationDenied("This opportunity is not awaiting Sales Manager review.")

        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if ConcurrencyManager.has_conflict(updated_at, opportunity.updated_at):
            raise RuntimeError(
                "This opportunity has changed since you opened it. Refresh before deciding."
            )

        decision = str(decision or "").upper()
        if decision not in {"APPROVE", "REJECT"}:
            raise ValueError("Decision must be APPROVE or REJECT.")

        if decision == "REJECT":
            if not reason or not reason.strip():
                raise ValueError("A rejection reason is required.")
            opportunity.status = REJECTED_STATUS
            opportunity.is_active = False

            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action=OPPORTUNITY_REJECTED,
                description=f"Opportunity rejected. Reason: {reason.strip()}",
                user_id=user.user_id,
                commit=False,
            )
            NotificationService.queue(
                opportunity.created_by,
                OPPORTUNITY_REJECTED,
                "Opportunity",
                opportunity.opportunity_id,
                f"Opportunity '{opportunity.opportunity_name}' was rejected: {reason.strip()}",
            )
        else:
            if sales_owner_id is None:
                raise ValueError("sales_owner_id is required when approving.")
            sales_owner = User.query.filter_by(user_id=sales_owner_id).first()
            if not AuthorizationService.can_assign_sales_owner(
                user, active_role, opportunity, sales_owner
            ):
                raise AuthorizationDenied(
                    "Sales Owner must be an active, approved Sales Executive."
                )

            opportunity.sales_owner_id = sales_owner.user_id
            opportunity.status = APPROVED_STATUS
            opportunity.is_active = True

            existing_team = OpportunityTeam.query.filter_by(
                opportunity_id=opportunity.opportunity_id,
                user_id=sales_owner.user_id,
            ).first()
            if not existing_team:
                db.session.add(OpportunityTeam(
                    opportunity_id=opportunity.opportunity_id,
                    user_id=sales_owner.user_id,
                    role=SALES_EXECUTIVE,
                ))

            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action=OPPORTUNITY_APPROVED,
                description=f"Opportunity approved by Sales Manager. Sales Owner: {sales_owner.full_name}.",
                user_id=user.user_id,
                commit=False,
            )
            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action=SALES_OWNER_ASSIGNED,
                description=f"Sales Owner assigned to {sales_owner.full_name}.",
                user_id=user.user_id,
                commit=False,
            )
            NotificationService.queue(
                sales_owner.user_id,
                SALES_OWNER_ASSIGNED,
                "Opportunity",
                opportunity.opportunity_id,
                f"You are now the Sales Owner for '{opportunity.opportunity_name}'.",
            )

            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action=OPPORTUNITY_SENT_TO_PRE_SALES,
                description="Opportunity approved and handed to Pre-Sales Manager for technical team assignment.",
                user_id=user.user_id,
                commit=False,
            )
            presales_managers = User.query.filter(
                User.active.is_(True),
                User.status == STATUS_APPROVED,
                User.roles.any(role=PRE_SALES_MANAGER),
            ).all()
            for manager in presales_managers:
                NotificationService.queue(
                    manager.user_id,
                    OPPORTUNITY_SENT_TO_PRE_SALES,
                    "Opportunity",
                    opportunity.opportunity_id,
                    "Opportunity '{}' was approved and requires technical team assignment.".format(opportunity.opportunity_name),
                )

        db.session.commit()
        return opportunity

    @staticmethod
    def transition_stage(opportunity_id, target_stage_id, user, active_role, remarks=None):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        return StageService.transition_stage(
            opportunity=opportunity,
            target_stage_id=target_stage_id,
            user=user,
            active_role=active_role,
            remarks=remarks,
        )

    @staticmethod
    def get_stage_history(opportunity_id, user, active_role):
        opportunity = OpportunityService.get_by_id(opportunity_id, user, active_role)
        if not opportunity:
            return None
        return StageService.get_history(opportunity_id)

    @staticmethod
    def delete_opportunity(opportunity_id, user, active_role):
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return False
        if not AuthorizationService.can_delete_opportunity(user, active_role, opportunity):
            raise AuthorizationDenied("Opportunity deletion is not permitted.")
        OpportunityRepository.delete(opportunity)
        return True
