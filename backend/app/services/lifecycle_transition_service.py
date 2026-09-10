"""Authoritative Deal Room v2 opportunity lifecycle transition engine."""
from sqlalchemy import update
from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.roles import (
    ADMIN,
    LEADERSHIP,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
)


from app.constants.stages import (
    LIFECYCLE_STAGES, OPERATIONAL_STATUSES,
)
from app.database import db
from app.models.opportunity.opportunity import Opportunity
from app.models.auth.user import User
from app.models.opportunity.stage_history import StageHistory
from app.repositories.stage_repository import StageRepository
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.closed_won_request import ClosedWonRequest


FORWARD_TRANSITIONS = {
    "Lead": {"Qualified"},
    "Qualified": {"RFX"},
    "RFX": {"POC"},
    "POC": {"Negotiations"},
    "Negotiations": {"Delivery"},
    "Delivery": set(),
}



class TransitionConflict(RuntimeError):
    """Current state/version no longer matches the caller's expectation."""


class TransitionInvalid(ValueError):
    """Requested action is not valid for the current state."""


class LifecycleTransitionService:
    """Single mutation authority for opportunity lifecycle/outcome/status."""

    _PRECONDITIONS = {}

    @classmethod
    def register_precondition(cls, from_stage, to_stage, validator):
        """Register a later-domain validator without creating a second state machine."""
        if from_stage not in LIFECYCLE_STAGES or to_stage not in LIFECYCLE_STAGES:
            raise ValueError("Precondition stages must be valid v2 lifecycle stages.")
        if not callable(validator):
            raise TypeError("Lifecycle precondition must be callable.")
        cls._PRECONDITIONS[(from_stage, to_stage)] = validator

    @classmethod
    def clear_precondition(cls, from_stage, to_stage):
        cls._PRECONDITIONS.pop((from_stage, to_stage), None)

    @staticmethod
    def _stage_id(lifecycle_stage):
        stage = StageRepository.get_by_name(lifecycle_stage)
        return stage.stage_id if stage else None

    @staticmethod
    def _normalize_lifecycle(opportunity):
        return opportunity.lifecycle_stage if opportunity.lifecycle_stage in LIFECYCLE_STAGES else None

    @staticmethod
    def _load(opportunity_id):
        return Opportunity.query.filter_by(opportunity_id=opportunity_id).with_for_update().first()

    @staticmethod
    def _check_expected_version(opportunity, expected_version):
        try:
            expected = int(expected_version)
        except (TypeError, ValueError):
            raise TransitionInvalid("expected_version is required and must be an integer.")
        if expected != opportunity.row_version:
            raise TransitionConflict("Opportunity version is stale. Refresh before retrying.")

    @staticmethod
    def assert_opportunity_open_for_mutation(opportunity):
        if not opportunity or opportunity.operational_status == "Closed" or opportunity.outcome in {"Closed Won", "Closed Lost"}:
            raise TransitionConflict("Opportunity is closed and locked for normal mutation.")

    @staticmethod
    def _authorize_stage(user, active_role, opportunity, target):
        if not AuthorizationService.can_change_lifecycle_stage(user, active_role, opportunity, target):
            raise AuthorizationDenied("This active role cannot change the opportunity lifecycle stage.")

    @staticmethod
    def _authorize_close(user, active_role, opportunity, won):
        if not AuthorizationService.can_close_opportunity(user, active_role, opportunity, won=won):
            if won and active_role == SOLUTION_ENGINEER:
                raise AuthorizationDenied("Solution Engineer Closed Won requires Pre-Sales Manager approval.")
            raise AuthorizationDenied("This active role cannot close the opportunity.")

    @staticmethod
    def _write_stage_history(opportunity, previous_stage, next_stage, user, active_role, version, remarks=None):
        stage_id = LifecycleTransitionService._stage_id(next_stage)
        if stage_id is None:
            raise TransitionInvalid(f"Lifecycle stage '{next_stage}' is not configured.")
        db.session.add(StageHistory(
            opportunity_id=opportunity.opportunity_id,
            stage_id=stage_id,
            from_lifecycle_stage=previous_stage,
            to_lifecycle_stage=next_stage,
            changed_by=user.user_id if user else None,
            actor_active_role=active_role,
            version=version,
            remarks=remarks,
        ))

    @staticmethod
    def _touch_state(opportunity, *, lifecycle_stage=None, outcome=None, operational_status=None, review_status=None,
                     lost_reason=None, lost_explanation=None, final_revenue=None, sync_legacy=True):
        values = {"row_version": Opportunity.row_version + 1}
        if lifecycle_stage is not None:
            values["lifecycle_stage"] = lifecycle_stage
            stage_id = LifecycleTransitionService._stage_id(lifecycle_stage)
            if stage_id is None:
                raise TransitionInvalid(f"Lifecycle stage '{lifecycle_stage}' is not configured.")
            values["stage_id"] = stage_id
        if outcome is not None:
            values["outcome"] = outcome
        if operational_status is not None:
            values["operational_status"] = operational_status
            if sync_legacy:
                values["status"] = operational_status
                values["is_active"] = operational_status != "Closed"
        if review_status is not None:
            values["review_status"] = review_status
        if lost_reason is not None:
            values["lost_reason"] = lost_reason
        if lost_explanation is not None:
            values["lost_explanation"] = lost_explanation
        if final_revenue is not None:
            values["final_revenue"] = final_revenue
        result = db.session.execute(
            update(Opportunity)
            .where(Opportunity.opportunity_id == opportunity.opportunity_id,
                   Opportunity.row_version == opportunity.row_version)
            .values(**values)
        )
        if result.rowcount != 1:
            raise TransitionConflict("Opportunity version is stale. Refresh before retrying.")
        db.session.expire(opportunity)
        db.session.refresh(opportunity)
        return opportunity

    @staticmethod
    def transition(opportunity_id, target_stage, expected_version, user, active_role, *, remarks=None, precondition=None):
        if target_stage not in LIFECYCLE_STAGES:
            raise TransitionInvalid("Invalid lifecycle stage.")
        opportunity = LifecycleTransitionService._load(opportunity_id)
        if not opportunity:
            return None
        LifecycleTransitionService.assert_opportunity_open_for_mutation(opportunity)
        current = LifecycleTransitionService._normalize_lifecycle(opportunity)
        if not current:
            raise TransitionInvalid("Opportunity has no mappable lifecycle stage.")
        LifecycleTransitionService._authorize_stage(user, active_role, opportunity, target_stage)
        LifecycleTransitionService._check_expected_version(opportunity, expected_version)
        if target_stage not in FORWARD_TRANSITIONS.get(current, set()):
            raise TransitionInvalid(f"Transition from {current} to {target_stage} is not allowed.")
        if current == "Negotiations" and target_stage == "Delivery":
            raise AuthorizationDenied("Negotiations to Delivery is the final Closed Won approval gate; use explicit Closed Won approval.")
        elif current == "RFX" and target_stage == "POC":
            from app.models.phase2 import RFXContext
            ctx = RFXContext.query.filter_by(opportunity_id=opportunity.opportunity_id).first()
            if not ctx or not ctx.drive_link:
                raise TransitionInvalid("A Google Drive link is required when moving RFX to POC.")
            validator = precondition or LifecycleTransitionService._PRECONDITIONS.get((current, target_stage))
            if validator:
                validator(opportunity)
            LifecycleTransitionService._touch_state(
                opportunity, lifecycle_stage=target_stage, outcome="Open", operational_status="Active", sync_legacy=True
            )
        elif current == "POC" and target_stage == "Negotiations":
            from app.models.opportunity.poc_tracker import POCTracker
            valid_poc = POCTracker.query.filter(
                POCTracker.opportunity_id == opportunity.opportunity_id,
                POCTracker.status == "Completed",
                POCTracker.result_view_link.isnot(None),
            ).first()
            if not valid_poc:
                raise TransitionInvalid("A completed POC with a result/view link is required before Negotiations.")
            validator = precondition or LifecycleTransitionService._PRECONDITIONS.get((current, target_stage))
            if validator:
                validator(opportunity)
            LifecycleTransitionService._touch_state(
                opportunity, lifecycle_stage=target_stage, outcome="Open", operational_status="Active", sync_legacy=True
            )
        else:
            validator = precondition or LifecycleTransitionService._PRECONDITIONS.get((current, target_stage))
            if validator:
                validator(opportunity)
            LifecycleTransitionService._touch_state(
                opportunity, lifecycle_stage=target_stage, outcome="Open", operational_status="Active", sync_legacy=True
            )
        LifecycleTransitionService._write_stage_history(opportunity, current, target_stage, user, active_role, opportunity.row_version, remarks)
        ActivityService.log("Opportunity", opportunity.opportunity_id, "OPPORTUNITY_STAGE_CHANGED",
                            f"Lifecycle changed from '{current}' to '{target_stage}'.", user.user_id, commit=False, active_role=active_role)
        # Reuse the single notification architecture for Phase 2 stage events.
        role_by_stage = {"Qualified": SALES_MANAGER, "RFX": PRE_SALES_MANAGER, "POC": PRE_SALES_MANAGER, "Negotiations": PRE_SALES_MANAGER, "Delivery": DELIVERY_MANAGER}
        notify_role = role_by_stage.get(target_stage)
        if notify_role:
            recipients = User.query.filter(User.active.is_(True), User.status=="APPROVED", User.roles.any(role=notify_role)).all()
            event = "OPPORTUNITY_QUALIFIED" if target_stage=="Qualified" else ("RFX_ENTERED" if target_stage=="RFX" else ("NEGOTIATIONS_ENTERED" if target_stage=="Negotiations" else "DELIVERY_PROJECT_CREATED" if target_stage=="Delivery" else "POC_READY_FOR_REVIEW"))
            for recipient in recipients:
                NotificationService.queue(recipient.user_id, event, "Opportunity", opportunity.opportunity_id, f"Opportunity '{opportunity.opportunity_name}' entered {target_stage}.")
        db.session.commit()
        return opportunity

    @staticmethod
    def submit_lead(opportunity_id, expected_version, user, active_role):
        opportunity = LifecycleTransitionService._load(opportunity_id)
        if not opportunity:
            return None
        LifecycleTransitionService.assert_opportunity_open_for_mutation(opportunity)
        if active_role not in {SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST, LEADERSHIP}:
            raise AuthorizationDenied("This active role cannot submit a Lead for review.")
        if LifecycleTransitionService._normalize_lifecycle(opportunity) != "Lead":
            raise TransitionInvalid("Only a Lead can be submitted for Sales Manager review.")
        if opportunity.review_status != "Draft":
            raise TransitionInvalid("Only a draft Lead can be submitted for Sales Manager review.")
        if opportunity.created_by != user.user_id:
            raise AuthorizationDenied("Only the Deal Finder can submit the Lead for review.")
        LifecycleTransitionService._check_expected_version(opportunity, expected_version)
        if not opportunity.description or not opportunity.description.strip():
            raise TransitionInvalid("Description is required before submitting the Lead.")
        if not getattr(opportunity, "pain_points", None):
            raise TransitionInvalid("Pain points are required before submitting the Lead.")
        if not Stakeholder.query.filter_by(opportunity_id=opportunity.opportunity_id).first():
            raise TransitionInvalid("At least one stakeholder is required before submitting the Lead.")
        try:
            LifecycleTransitionService._touch_state(opportunity, review_status="Pending Sales Manager Review")
            ActivityService.log("Opportunity", opportunity.opportunity_id, "OPPORTUNITY_SUBMITTED_FOR_REVIEW",
                                "Lead submitted for Sales Manager review.", user.user_id, commit=False, active_role=active_role)
            # The existing notification infrastructure is the event delivery
            # boundary. Recipient selection is intentionally role-scoped.
            managers = User.query.filter(
                User.active.is_(True), User.status == "APPROVED", User.roles.any(role=SALES_MANAGER)
            ).all()
            for manager in managers:
                NotificationService.queue(
                    manager.user_id, "OPPORTUNITY_SUBMITTED_FOR_REVIEW", "Opportunity",
                    opportunity.opportunity_id,
                    f"Lead '{opportunity.opportunity_name}' is awaiting Sales Manager review.",
                )
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def approve_lead(opportunity_id, expected_version, sales_owner_id, user, active_role, assignment_validator=None, editable_fields=None):
        opportunity = LifecycleTransitionService._load(opportunity_id)
        if not opportunity:
            return None
        if active_role not in {SALES_MANAGER, LEADERSHIP}:
            raise AuthorizationDenied("Only Sales Manager or Leadership can approve a Lead.")
        if LifecycleTransitionService._normalize_lifecycle(opportunity) != "Lead" or opportunity.review_status != "Pending Sales Manager Review":
            raise TransitionInvalid("Lead is not awaiting Sales Manager review.")
        if not sales_owner_id:
            raise TransitionInvalid("Sales Executive assignment is required for Lead approval.")
        LifecycleTransitionService._check_expected_version(opportunity, expected_version)
        try:
            if assignment_validator:
                assignment_validator(opportunity, sales_owner_id)
            for field in ("opportunity_name", "description", "pain_points", "probability", "expected_close_date"):
                if editable_fields and field in editable_fields:
                    value = editable_fields[field]
                    if field == "opportunity_name" and value is not None:
                        value = value.strip()
                    setattr(opportunity, field, value)
            opportunity.sales_owner_id = sales_owner_id
            LifecycleTransitionService._touch_state(
                opportunity, lifecycle_stage="Qualified", outcome="Open",
                operational_status="Active", review_status="Approved"
            )
            LifecycleTransitionService._write_stage_history(
                opportunity, "Lead", "Qualified", user, active_role, opportunity.row_version,
                "Lead approved; Sales Executive assigned."
            )
            ActivityService.log("Opportunity", opportunity.opportunity_id, "OPPORTUNITY_APPROVED",
                                "Lead approved and moved to Qualified.", user.user_id, commit=False, active_role=active_role)
            ActivityService.log("Opportunity", opportunity.opportunity_id, "SALES_OWNER_ASSIGNED",
                                f"Sales Executive {sales_owner_id} assigned during initial approval.", user.user_id, commit=False, active_role=active_role)
            NotificationService.queue(
                sales_owner_id, "SALES_OWNER_ASSIGNED", "Opportunity", opportunity.opportunity_id,
                f"You have been assigned as Sales Executive for '{opportunity.opportunity_name}'."
            )
            # Downstream Pre-Sales notification uses the existing notification
            # type; recipient discovery remains a later-domain concern.
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def close_lost(opportunity_id, expected_version, reason, explanation, user, active_role):
        opportunity = LifecycleTransitionService._load(opportunity_id)
        if not opportunity:
            return None
        try:
            LifecycleTransitionService.assert_opportunity_open_for_mutation(opportunity)
            LifecycleTransitionService._authorize_close(user, active_role, opportunity, False)
            LifecycleTransitionService._check_expected_version(opportunity, expected_version)
            if LifecycleTransitionService._normalize_lifecycle(opportunity) == "Lead" and opportunity.review_status != "Pending Sales Manager Review":
                raise TransitionInvalid("Initial Lead closure is only available during Sales Manager review.")
            if not reason or not str(reason).strip():
                raise TransitionInvalid("A Closed Lost standard reason is required.")
            reason = str(reason).strip()
            if reason.lower() == "other" and not explanation:
                raise TransitionInvalid("Explanation is required when Closed Lost reason is Other.")
            if explanation is not None and not str(explanation).strip():
                explanation = None
            current = LifecycleTransitionService._normalize_lifecycle(opportunity)
            if opportunity.closed_won_request and opportunity.closed_won_request.status == "Pending":
                from datetime import datetime
                opportunity.closed_won_request.status = "Rejected"
                opportunity.closed_won_request.resolved_by = user.user_id
                opportunity.closed_won_request.resolved_active_role = active_role
                opportunity.closed_won_request.resolution_reason = "Closed Lost superseded the pending Closed Won request."
                opportunity.closed_won_request.resolved_at = datetime.utcnow()
            LifecycleTransitionService._touch_state(
                opportunity,
                outcome="Closed Lost",
                operational_status="Closed",
                lost_reason=reason,
                lost_explanation=(str(explanation).strip() if explanation else None),
                sync_legacy=True,
            )
            ActivityService.log(
                "Opportunity", opportunity.opportunity_id, "OPPORTUNITY_CLOSED_LOST",
                f"Opportunity closed lost. Previous stage: '{current}'. Reason: {reason}.",
                user.user_id, commit=False, active_role=active_role,
            )
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def _close_won_locked(cls, opportunity, user, active_role):
        """Close a locked opportunity without committing; caller owns the transaction."""
        cls.assert_opportunity_open_for_mutation(opportunity)
        cls._authorize_close(user, active_role, opportunity, True)
        current = cls._normalize_lifecycle(opportunity)
        if current == "Lead" and opportunity.review_status != "Pending Sales Manager Review":
            raise TransitionInvalid("Initial Lead closure is only available during Sales Manager review.")
        if opportunity.final_revenue is not None:
            raise TransitionInvalid("Final Revenue has already been established and cannot be overwritten.")
        if opportunity.closed_won_request and opportunity.closed_won_request.status == "Pending":
            from datetime import datetime
            opportunity.closed_won_request.status = "Approved"
            opportunity.closed_won_request.resolved_by = user.user_id
            opportunity.closed_won_request.resolved_active_role = active_role
            opportunity.closed_won_request.resolution_reason = "Closed Won approved directly through the authorized closure workflow."
            opportunity.closed_won_request.resolved_at = datetime.utcnow()
        target = "Delivery" if current == "Negotiations" else current
        cls._touch_state(
            opportunity,
            lifecycle_stage=target,
            outcome="Closed Won",
            operational_status="Closed",
            review_status="Approved",
            final_revenue=opportunity.estimated_value,
            sync_legacy=True,
        )
        if target != current:
            cls._write_stage_history(
                opportunity, current, target, user, active_role, opportunity.row_version,
                "Final Closed Won approval moved Negotiations to Delivery.",
            )
        ActivityService.log(
            "Opportunity", opportunity.opportunity_id, "OPPORTUNITY_CLOSED_WON",
            f"Opportunity closed won. Previous stage: '{current}'. Final Revenue established at {opportunity.final_revenue}.",
            user.user_id, commit=False, active_role=active_role,
        )
        ActivityService.log(
            "Opportunity", opportunity.opportunity_id, "FINAL_REVENUE_SNAPSHOTTED",
            f"Final Revenue snapshot equals the server-side current Opportunity Value: {opportunity.final_revenue}.",
            user.user_id, commit=False, active_role=active_role,
        )
        from app.services.phase2_service import Phase2Service
        Phase2Service.create_delivery_project(opportunity, user, active_role)
        return opportunity

    @classmethod
    def close_won(cls, opportunity_id, expected_version, user, active_role):
        opportunity = cls._load(opportunity_id)
        if not opportunity:
            return None
        try:
            cls._check_expected_version(opportunity, expected_version)
            result = cls._close_won_locked(opportunity, user, active_role)
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def request_closed_won(opportunity_id, expected_version, user, active_role):
        opportunity = LifecycleTransitionService._load(opportunity_id)
        if not opportunity:
            return None
        try:
            LifecycleTransitionService.assert_opportunity_open_for_mutation(opportunity)
            if not AuthorizationService.can_request_closed_won(user, active_role, opportunity):
                raise AuthorizationDenied("Only an assigned Solution Engineer in an open post-Lead stage can request Closed Won.")
            LifecycleTransitionService._check_expected_version(opportunity, expected_version)
            current_request = opportunity.closed_won_request
            if current_request and current_request.status == "Pending":
                raise TransitionInvalid("A Closed Won request is already pending.")
            if current_request and current_request.status == "Approved":
                raise TransitionInvalid("Closed Won has already been approved for this opportunity.")
            if current_request:
                from datetime import datetime
                current_request.status = "Pending"
                current_request.requested_by = user.user_id
                current_request.requested_active_role = active_role
                current_request.requested_at = datetime.utcnow()
                current_request.resolved_by = None
                current_request.resolved_active_role = None
                current_request.resolution_reason = None
                current_request.resolved_at = None
            else:
                current_request = ClosedWonRequest(
                    opportunity_id=opportunity.opportunity_id,
                    requested_by=user.user_id,
                    requested_active_role=active_role,
                    status="Pending",
                )
                db.session.add(current_request)
            LifecycleTransitionService._touch_state(opportunity, review_status="Approved")
            ActivityService.log(
                "Opportunity", opportunity.opportunity_id, "CLOSED_WON_REQUESTED",
                f"Solution Engineer requested Closed Won from stage '{opportunity.lifecycle_stage}'.",
                user.user_id, commit=False, active_role=active_role,
            )
            managers = User.query.filter(
                User.active.is_(True),
                User.status == "APPROVED",
                User.roles.any(role=PRE_SALES_MANAGER),
            ).all()
            for manager in managers:
                NotificationService.queue(
                    manager.user_id, "CLOSED_WON_REQUESTED", "Opportunity",
                    opportunity.opportunity_id,
                    f"Closed Won approval is requested for '{opportunity.opportunity_name}'.",
                )
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def resolve_closed_won_request(opportunity_id, expected_version, approve, reason, user, active_role):
        opportunity = LifecycleTransitionService._load(opportunity_id)
        if not opportunity:
            return None
        try:
            LifecycleTransitionService.assert_opportunity_open_for_mutation(opportunity)
            if not AuthorizationService.can_approve_closed_won_request(user, active_role, opportunity):
                raise AuthorizationDenied("Only the active Pre-Sales Manager role can resolve a Closed Won request.")
            LifecycleTransitionService._check_expected_version(opportunity, expected_version)
            request = opportunity.closed_won_request
            if not request or request.status != "Pending":
                raise TransitionInvalid("There is no pending Closed Won request for this opportunity.")
            if approve:
                request.status = "Approved"
                request.resolved_by = user.user_id
                request.resolved_active_role = active_role
                request.resolution_reason = (str(reason).strip() if reason else None)
                from datetime import datetime
                request.resolved_at = datetime.utcnow()
                result = LifecycleTransitionService._close_won_locked(opportunity, user, active_role)
                ActivityService.log(
                    "Opportunity", opportunity.opportunity_id, "CLOSED_WON_REQUEST_APPROVED",
                    "Closed Won request approved by Pre-Sales Manager.",
                    user.user_id, commit=False, active_role=active_role,
                )
                NotificationService.queue(
                    request.requested_by, "CLOSED_WON_REQUEST_APPROVED", "Opportunity",
                    opportunity.opportunity_id,
                    f"Closed Won request for '{opportunity.opportunity_name}' was approved.",
                )
                db.session.commit()
                return result
            if reason is None or not str(reason).strip():
                raise TransitionInvalid("A rejection reason is required for a Closed Won request.")
            request.status = "Rejected"
            request.resolved_by = user.user_id
            request.resolved_active_role = active_role
            request.resolution_reason = str(reason).strip()
            from datetime import datetime
            request.resolved_at = datetime.utcnow()
            ActivityService.log(
                "Opportunity", opportunity.opportunity_id, "CLOSED_WON_REQUEST_REJECTED",
                f"Closed Won request rejected. Reason: {request.resolution_reason}",
                user.user_id, commit=False, active_role=active_role,
            )
            NotificationService.queue(
                request.requested_by, "CLOSED_WON_REQUEST_REJECTED", "Opportunity",
                opportunity.opportunity_id,
                f"Closed Won request for '{opportunity.opportunity_name}' was rejected.",
            )
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def set_operational_status(opportunity_id, target_status, expected_version, user, active_role):
        if target_status not in OPERATIONAL_STATUSES:
            raise TransitionInvalid("Invalid operational status.")
        opportunity = LifecycleTransitionService._load(opportunity_id)
        if not opportunity:
            return None
        if active_role == ADMIN:
            raise AuthorizationDenied("Admin cannot change opportunity operational status.")
        if opportunity.operational_status == "Closed":
            raise TransitionConflict("Opportunity is closed and locked for normal mutation.")
        if target_status == "Closed":
            raise TransitionInvalid("Use an explicit closure action to close an opportunity.")
        if target_status == opportunity.operational_status:
            return opportunity
        if {opportunity.operational_status, target_status} != {"Active", "Stalled"}:
            raise TransitionInvalid(f"Operational status transition to {target_status} is not allowed.")
        if active_role not in {SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, LEADERSHIP}:
            raise AuthorizationDenied("This active role cannot change operational status.")
        LifecycleTransitionService._check_expected_version(opportunity, expected_version)
        LifecycleTransitionService._touch_state(opportunity, operational_status=target_status, sync_legacy=True)
        ActivityService.log("Opportunity", opportunity.opportunity_id, "OPPORTUNITY_STATUS_CHANGED",
                            f"Operational status changed to '{target_status}'.", user.user_id, commit=False)
        db.session.commit()
        return opportunity
