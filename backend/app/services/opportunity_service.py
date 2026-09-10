from datetime import datetime

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.activity_types import (
    OPPORTUNITY_APPROVED,
    OPPORTUNITY_QUALIFIED,
    OPPORTUNITY_SUBMITTED_FOR_REVIEW,
    SALES_OWNER_ASSIGNED,
    OPPORTUNITY_SENT_TO_PRE_SALES,
    PRE_SALES_ASSIGNMENT_FINALIZED,
    OPPORTUNITY_STAGE_CHANGED,
    SOLUTION_ENGINEER_ASSIGNED,
)
from app.constants.auth_constants import STATUS_APPROVED
from app.constants.roles import LEADERSHIP, PRE_SALES_MANAGER, SALES_EXECUTIVE, SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST
from app.constants.stages import (
    ACTIVE_STATUS,
    APPROVED_STATUS,
    INITIAL_STAGE_NAME,
    OPEN_STATUS,
    PENDING_SALES_MANAGER_REVIEW_STATUS,
)
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stakeholder import Stakeholder
from app.repositories.opportunity_repository import OpportunityRepository
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService
from app.services.stage_service import StageService
from app.services.lifecycle_transition_service import LifecycleTransitionService, TransitionConflict, TransitionInvalid
from app.services.opportunity_value_service import OpportunityValueService
from app.repositories.stage_repository import StageRepository
from app.utils.concurrency import ConcurrencyManager


class OpportunityService:

    @staticmethod
    def create_opportunity(data, user, active_role):
        if not AuthorizationService.can_create_opportunity(user, active_role):
            raise AuthorizationDenied("You are not authorized to create opportunities.")

        account = Account.query.filter_by(account_id=data["account_id"]).first()
        if not account:
            raise ValueError("Canonical account does not exist.")
        if account.status == "Banned":
            raise ValueError("this account is banned")
        if account.status != "Active" or not account.is_active:
            raise ValueError("This account is not active and cannot be selected for a new opportunity.")
        if not AuthorizationService.can_view_account(user, active_role, account):
            raise AuthorizationDenied("You are not authorized to use this account.")

        if OpportunityRepository.exists(data["opportunity_name"], data["account_id"]):
            raise ValueError("Opportunity already exists for this account.")

        initial_stage = StageService.get_initial_stage()
        if not initial_stage:
            raise RuntimeError(f"Required stage '{INITIAL_STAGE_NAME}' is not configured.")

        opportunity = Opportunity(
            account_id=data["account_id"],
            # `created_by` is the persisted Deal Finder. It is write-once: all
            # later mutation schemas/services exclude it.
            created_by=user.user_id,
            sales_owner_id=None,
            stage_id=initial_stage.stage_id,
            lifecycle_stage="Lead",
            outcome="Open",
            operational_status="Active",
            review_status="Draft",
            row_version=1,
            opportunity_name=data["opportunity_name"].strip(),
            description=data.get("description"),
            pain_points=data.get("pain_points"),
            estimated_value=data["estimated_value"],
            probability=data.get("probability", 0),
            expected_close_date=data.get("expected_close_date"),
            status=ACTIVE_STATUS,
            is_active=True,
        )

        try:
            db.session.add(opportunity)
            db.session.flush()
            db.session.add(OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=user.user_id,
                role=active_role,
            ))
            StageService.record_initial_stage(opportunity, user.user_id)
            OpportunityValueService.record_initial_value(opportunity, user, active_role)
            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action="OPPORTUNITY_CREATED",
                description=(f"Opportunity '{opportunity.opportunity_name}' created; "
                             f"Deal Finder is {user.full_name}."),
                user_id=user.user_id,
                commit=False,
                active_role=active_role,
            )
            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action="DEAL_FINDER_ASSIGNED",
                description=f"Deal Finder assigned permanently to {user.full_name} at creation.",
                user_id=user.user_id,
                commit=False,
                active_role=active_role,
            )
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all(user, active_role):
        return OpportunityRepository.get_all(
            AuthorizationService.opportunity_query(user, active_role)
        )

    @staticmethod
    def get_pending_review(user, active_role):
        if not AuthorizationService.can_view_pending_review(user, active_role):
            raise AuthorizationDenied("Only Sales Manager or Leadership can view the review queue.")
        return OpportunityRepository.get_pending_sales_manager_review(
            AuthorizationService.opportunity_query(user, active_role)
        )

    @staticmethod
    def get_eligible_sales_owners(user, active_role):
        if not AuthorizationService.can_view_pending_review(user, active_role):
            raise AuthorizationDenied("Only Sales Manager or Leadership can view Sales Owner candidates.")
        return OpportunityRepository.get_eligible_sales_owners()

    @staticmethod
    def get_pending_pre_sales_assignment(user, active_role):
        if not AuthorizationService.can_view_pending_pre_sales_assignment(user, active_role):
            raise AuthorizationDenied("Only a Pre-Sales Manager can view the pending assignment queue.")
        return OpportunityRepository.get_pending_pre_sales_assignment()

    @staticmethod
    def get_eligible_pre_sales_users(user, active_role, role):
        if not AuthorizationService.can_view_pending_pre_sales_assignment(user, active_role):
            raise AuthorizationDenied("Only a Pre-Sales Manager can view technical assignment candidates.")
        if role != SOLUTION_ENGINEER:
            raise ValueError("The only technical assignment role is Solution Engineer.")
        return OpportunityRepository.get_eligible_users(SOLUTION_ENGINEER)

    @staticmethod
    def finalize_pre_sales_assignment(
        opportunity_id, solution_engineer_ids, delivery_ids=None, updated_at=None, user=None, active_role=None
    ):
        if active_role != PRE_SALES_MANAGER:
            raise AuthorizationDenied("Only the active Pre-Sales Manager role can finalize technical assignment.")
        opportunity = OpportunityRepository.get_by_id(opportunity_id)
        if not opportunity:
            return None
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return None
        if OpportunityTeam.query.filter(
            OpportunityTeam.opportunity_id == opportunity.opportunity_id,
            OpportunityTeam.role == SOLUTION_ENGINEER,
        ).first():
            raise RuntimeError("Technical assignment has already been finalized.")
        if not AuthorizationService.can_finalize_pre_sales_assignment(user, active_role, opportunity):
            raise RuntimeError("Opportunity is not awaiting Pre-Sales assignment.")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if ConcurrencyManager.has_conflict(updated_at, opportunity.updated_at):
            raise RuntimeError("This opportunity has changed since you opened it. Refresh before assigning the technical team.")

        ids = [int(uid) for uid in (solution_engineer_ids or [])]
        ids.extend(int(uid) for uid in (delivery_ids or []))
        ids = list(dict.fromkeys(ids))
        if not ids:
            raise ValueError("At least one Solution Engineer is required.")

        users = {u.user_id: u for u in User.query.filter(User.user_id.in_(ids)).all()}
        if len(users) != len(ids):
            raise ValueError("One or more selected users do not exist.")
        for uid in ids:
            candidate = users.get(uid)
            if not candidate or not candidate.active or candidate.status != STATUS_APPROVED or not candidate.has_role(SOLUTION_ENGINEER):
                raise ValueError(f"User {uid} is not an eligible Solution Engineer.")

        existing_ids = {row.user_id for row in OpportunityTeam.query.filter_by(opportunity_id=opportunity.opportunity_id).all()}
        if existing_ids.intersection(ids):
            raise ValueError("A selected user is already assigned to this opportunity.")

        updated_rows = Opportunity.query.filter(
            Opportunity.opportunity_id == opportunity.opportunity_id,
            Opportunity.operational_status == ACTIVE_STATUS,
            Opportunity.review_status == APPROVED_STATUS,
            Opportunity.sales_owner_id.isnot(None),
            Opportunity.is_active.is_(True),
        ).update({"status": ACTIVE_STATUS}, synchronize_session=False)
        if updated_rows != 1:
            db.session.rollback()
            raise RuntimeError("Technical assignment has already been finalized or the opportunity is no longer assignable.")
        db.session.expire(opportunity, ["status", "updated_at"])
        db.session.refresh(opportunity)

        try:
            for uid in ids:
                db.session.add(OpportunityTeam(
                    opportunity_id=opportunity.opportunity_id,
                    user_id=uid,
                    role=SOLUTION_ENGINEER,
                ))
            ActivityService.log(
                entity_type="Opportunity",
                entity_id=opportunity.opportunity_id,
                action=PRE_SALES_ASSIGNMENT_FINALIZED,
                description=(f"Technical team assigned. Solution Engineers: "
                             f"{', '.join(users[uid].full_name for uid in ids)}."),
                user_id=user.user_id,
                commit=False,
            )
            for uid in ids:
                ActivityService.log(
                    entity_type="Opportunity",
                    entity_id=opportunity.opportunity_id,
                    action=SOLUTION_ENGINEER_ASSIGNED,
                    description=f"{users[uid].full_name} assigned as Solution Engineer.",
                    user_id=user.user_id,
                    commit=False,
                )
                NotificationService.queue(
                    uid, SOLUTION_ENGINEER_ASSIGNED, "Opportunity", opportunity.opportunity_id,
                    f"You have been assigned to Opportunity '{opportunity.opportunity_name}' as Solution Engineer.",
                )
            db.session.commit()
            return opportunity
        except (IntegrityError, OperationalError):
            db.session.rollback()
            raise RuntimeError("Technical assignment could not be finalized because the opportunity was changed concurrently.")
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

        if "estimated_value" in data or "final_revenue" in data:
            raise ValueError("Opportunity Value changes must use the dedicated value endpoint.")

        expected_version = data.pop("expected_version", None)
        try:
            expected_version = int(expected_version)
        except (TypeError, ValueError):
            raise ValueError("expected_version is required and must be an integer.")

        if expected_version != opportunity.row_version:
            raise RuntimeError("Opportunity version is stale. Refresh before retrying.")

        allowed_fields = {"opportunity_name", "description", "pain_points", "probability", "expected_close_date"}
        values = {key: value for key, value in data.items() if key in allowed_fields}
        if not values:
            raise ValueError("No permitted opportunity fields were supplied.")
        values["row_version"] = Opportunity.row_version + 1
        result = db.session.execute(
            update(Opportunity)
            .where(Opportunity.opportunity_id == opportunity.opportunity_id,
                   Opportunity.row_version == expected_version,
                   Opportunity.operational_status != "Closed")
            .values(**values)
        )
        if result.rowcount != 1:
            db.session.rollback()
            raise RuntimeError("Opportunity version is stale. Refresh before retrying.")
        db.session.expire(opportunity)
        db.session.refresh(opportunity)
        ActivityService.log(
            entity_type="Opportunity", entity_id=opportunity.opportunity_id,
            action="OPPORTUNITY_REVIEW_FIELDS_UPDATED" if active_role in {SALES_MANAGER, LEADERSHIP} and opportunity.review_status == PENDING_SALES_MANAGER_REVIEW_STATUS else "UPDATE_OPPORTUNITY",
            description=f"Permitted opportunity fields updated by {user.full_name}.",
            user_id=user.user_id, commit=False, active_role=active_role,
        )
        db.session.commit()
        return opportunity

    @staticmethod
    def qualify_opportunity(opportunity_id, user, active_role):
        # Retained only as a compatibility facade. v2 qualification is the
        # Sales Manager Lead-approval action and cannot be performed by a
        # generic qualify endpoint.
        raise AuthorizationDenied("Lead qualification is performed by Sales Manager approval.")

    @staticmethod
    def submit_for_sales_manager_review(opportunity_id, user, active_role, expected_version):
        return LifecycleTransitionService.submit_lead(opportunity_id, expected_version, user, active_role)

    @staticmethod
    def review_opportunity(opportunity_id, decision, sales_owner_id, reason, expected_version, user, active_role, editable_fields=None):
        decision = str(decision or "").upper()
        if decision == "APPROVE":
            def validate_assignment(opportunity, owner_id):
                sales_owner = User.query.filter_by(user_id=owner_id).first()
                if not sales_owner:
                    raise AuthorizationDenied("Sales Executive does not exist.")
                if not AuthorizationService.can_assign_sales_owner(user, active_role, opportunity, sales_owner):
                    # Leadership is not governed by the manager's scoped helper.
                    if not (active_role == LEADERSHIP and sales_owner.active and sales_owner.status == STATUS_APPROVED and sales_owner.has_role(SALES_EXECUTIVE)):
                        raise AuthorizationDenied("Sales Owner must be an active, approved Sales Executive.")
                existing_team = OpportunityTeam.query.filter_by(
                    opportunity_id=opportunity.opportunity_id, user_id=owner_id, role=SALES_EXECUTIVE
                ).first()
                if not existing_team:
                    db.session.add(OpportunityTeam(
                        opportunity_id=opportunity.opportunity_id, user_id=owner_id, role=SALES_EXECUTIVE
                    ))
            return LifecycleTransitionService.approve_lead(
                opportunity_id, expected_version, sales_owner_id, user, active_role, validate_assignment,
                editable_fields=editable_fields or {},
            )
        if decision == "CLOSE_WON":
            return LifecycleTransitionService.close_won(opportunity_id, expected_version, user, active_role)
        if decision == "CLOSE_LOST":
            return LifecycleTransitionService.close_lost(opportunity_id, expected_version, reason, editable_fields.get("lost_explanation") if editable_fields else None, user, active_role)
        raise ValueError("Decision must be APPROVE, CLOSE_WON, or CLOSE_LOST.")

    @staticmethod
    def transition_stage(opportunity_id, target_stage_id, user, active_role, remarks=None, expected_version=None):
        if expected_version is None:
            raise TransitionInvalid("expected_version is required for lifecycle transitions.")
        target = StageRepository.get_by_id(target_stage_id)
        if not target:
            raise TransitionInvalid("Invalid opportunity stage.")
        lifecycle = target.stage_name
        return LifecycleTransitionService.transition(
            opportunity_id, lifecycle, expected_version, user, active_role, remarks=remarks
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
