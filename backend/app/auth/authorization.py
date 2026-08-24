from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import exists, or_, false

from app.constants.auth_constants import STATUS_APPROVED, STATUS_REVOKED
from app.constants.roles import (
    ADMIN,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
    is_valid_role,
    normalize_role,
)
from app.database import db
from app.models.account.account import Account
from app.models.account.oem_partner import OEMPartner
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stakeholder import Stakeholder
from app.models.system.audit_log import AuditLog
from app.models.opportunity.stage_master import StageMaster
from app.constants.poc_outcome import (POC_STATUS_DRAFT, POC_STATUS_APPROVED, POC_STATUS_IN_PROGRESS, POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED)


class AuthorizationDenied(PermissionError):
    """Authenticated user lacks the requested authorization."""


class Actions:
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class Resources:
    OPPORTUNITY = "opportunity"
    ACCOUNT = "account"
    STAKEHOLDER = "stakeholder"
    POC = "poc"
    ACTIVITY = "activity"
    OEM = "oem"
    DASHBOARD = "dashboard"


class AuthorizationService:
    """Central Phase-2 authorization and visibility policy layer."""

    IC_ROLES = {SALES_EXECUTIVE, SOLUTION_ENGINEER}

    @staticmethod
    def current_context():
        claims = get_jwt()
        identity = get_jwt_identity()

        try:
            user_id = int(identity)
        except (TypeError, ValueError):
            raise AuthorizationDenied("Invalid authenticated user.")

        user = User.query.filter_by(user_id=user_id).first()
        active_role = normalize_role(claims.get("active_role"))

        claims_version = get_jwt().get("auth_version")
        if not user:
            raise AuthorizationDenied("Authenticated user is not active.")
        if user.status == STATUS_REVOKED:
            raise AuthorizationDenied("Your access has been revoked.")
        if not user.active or user.status != STATUS_APPROVED:
            raise AuthorizationDenied("Authenticated user is not active.")
        if claims_version is None or int(claims_version) != int(user.auth_version):
            raise AuthorizationDenied("Session is stale. Please sign in again.")

        if not is_valid_role(active_role):
            raise AuthorizationDenied("A valid active role is required.")

        if not user.has_role(active_role):
            raise AuthorizationDenied("Active role is no longer assigned to this user.")

        g.auth_user = user
        g.active_role = active_role
        return user, active_role

    @staticmethod
    def opportunity_query(user, active_role):
        """Return only opportunities visible to the active role."""
        query = Opportunity.query

        if active_role == ADMIN:
            return query.filter(false())

        participation = exists().where(
            (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
            & (OpportunityTeam.user_id == user.user_id)
            & (OpportunityTeam.role == active_role)
        )

        if active_role in AuthorizationService.IC_ROLES:
            return query.filter(participation)

        if active_role == SALES_MANAGER:
            # Sales scope is the pre-handoff portion of the pipeline plus any
            # opportunity explicitly carrying a Sales Executive/Sales Owner.
            sales_team = exists().where(
                (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
                & (OpportunityTeam.role == SALES_EXECUTIVE)
            )
            # Phase 3 separates Sales Owner from OpportunityTeam. Any
            # opportunity with an assigned Sales Owner remains in Sales scope.
            assigned_sales_owner = Opportunity.sales_owner_id.isnot(None)
            pre_handoff = exists().where(
                (StageMaster.stage_id == Opportunity.stage_id)
                & (StageMaster.display_order <= 2)
            ).correlate_except(StageMaster)
            return query.filter(or_(sales_team, assigned_sales_owner, pre_handoff))

        if active_role == PRE_SALES_MANAGER:
            # Pre-Sales scope begins at Discovery and is also retained for
            # opportunities explicitly carrying technical/delivery members.
            technical_team = exists().where(
                (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
                & (OpportunityTeam.role == SOLUTION_ENGINEER)
            )
            pre_sales_stage = exists().where(
                (StageMaster.stage_id == Opportunity.stage_id)
                & (StageMaster.display_order >= 3)
            ).correlate_except(StageMaster)
            # Approved opportunities awaiting technical allocation are in
            # Pre-Sales scope even when their sales stage is still Qualification.
            awaiting_assignment = (
                (Opportunity.status == "Approved")
                & Opportunity.sales_owner_id.isnot(None)
                & ~exists().where(
                    (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
                    & (OpportunityTeam.role == SOLUTION_ENGINEER)
                )
            )
            return query.filter(or_(technical_team, pre_sales_stage, awaiting_assignment))

        return query.filter(false())

    @staticmethod
    def can_view_opportunity(user, active_role, opportunity):
        if not opportunity:
            return False
        return AuthorizationService.opportunity_query(user, active_role).filter(
            Opportunity.opportunity_id == opportunity.opportunity_id
        ).first() is not None

    @staticmethod
    def account_query(user, active_role):
        if active_role == ADMIN:
            return Account.query.filter(false())

        visible_opportunities = AuthorizationService.opportunity_query(user, active_role).with_entities(
            Opportunity.account_id
        ).subquery()
        return Account.query.filter(Account.account_id.in_(visible_opportunities))

    @staticmethod
    def can_view_account(user, active_role, account):
        return bool(account) and AuthorizationService.account_query(user, active_role).filter(
            Account.account_id == account.account_id
        ).first() is not None

    @staticmethod
    def can_view_stakeholder(user, active_role, stakeholder):
        return bool(stakeholder) and AuthorizationService.can_view_opportunity(
            user, active_role, stakeholder.opportunity
        )

    @staticmethod
    def can_view_poc(user, active_role, poc):
        return bool(poc) and AuthorizationService.can_view_opportunity(
            user, active_role, poc.opportunity
        )

    @staticmethod
    def can_view_oem(user, active_role, oem):
        return bool(oem) and AuthorizationService.account_query(user, active_role).filter(
            Account.account_id == oem.account_id
        ).first() is not None

    @staticmethod
    def can_view_activity(user, active_role, entity_type, entity_id):
        if active_role == ADMIN:
            return entity_type.lower() in {"admin", "user", "access"}

        if entity_type.lower() == "opportunity":
            opportunity = Opportunity.query.get(entity_id)
            return AuthorizationService.can_view_opportunity(user, active_role, opportunity)

        if entity_type.lower() == "account":
            account = Account.query.get(entity_id)
            return AuthorizationService.can_view_account(user, active_role, account)

        if entity_type.lower() == "stakeholder":
            stakeholder = Stakeholder.query.get(entity_id)
            return AuthorizationService.can_view_stakeholder(user, active_role, stakeholder)

        if entity_type.lower() in {"poc", "poctracker"}:
            poc = POCTracker.query.get(entity_id)
            return AuthorizationService.can_view_poc(user, active_role, poc)

        return False

    @staticmethod
    def can_qualify_opportunity(user, active_role, opportunity):
        return (
            active_role == SALES_EXECUTIVE
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and opportunity.created_by == user.user_id
            and opportunity.is_active
            and opportunity.status == "Open"
            and opportunity.current_stage is not None
            and opportunity.current_stage.stage_name == "Lead / Identified"
        )

    @staticmethod
    def can_submit_for_review(user, active_role, opportunity):
        return (
            active_role == SALES_EXECUTIVE
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and opportunity.created_by == user.user_id
            and opportunity.is_active
            and opportunity.status == "Open"
            and opportunity.current_stage is not None
            and opportunity.current_stage.stage_name == "Qualification"
        )

    @staticmethod
    def can_view_pending_review(user, active_role):
        return active_role == SALES_MANAGER

    @staticmethod
    def can_review_opportunity(user, active_role, opportunity):
        return (
            active_role == SALES_MANAGER
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and opportunity.is_active
            and opportunity.status == "Pending Sales Manager Review"
        )

    @staticmethod
    def can_approve_opportunity(user, active_role, opportunity):
        return AuthorizationService.can_review_opportunity(user, active_role, opportunity)

    @staticmethod
    def can_reject_opportunity(user, active_role, opportunity):
        return AuthorizationService.can_review_opportunity(user, active_role, opportunity)

    @staticmethod
    def can_assign_sales_owner(user, active_role, opportunity, sales_owner):
        return (
            AuthorizationService.can_approve_opportunity(user, active_role, opportunity)
            and bool(sales_owner)
            and sales_owner.active
            and sales_owner.status == STATUS_APPROVED
            and sales_owner.has_role(SALES_EXECUTIVE)
        )

    @staticmethod
    def can_reassign_sales_owner(user, active_role, opportunity):
        return False


    @staticmethod
    def can_view_pending_pre_sales_assignment(user, active_role):
        return active_role == PRE_SALES_MANAGER

    @staticmethod
    def can_finalize_pre_sales_assignment(user, active_role, opportunity):
        return (
            active_role == PRE_SALES_MANAGER
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and opportunity.is_active
            and opportunity.status == "Approved"
            and opportunity.sales_owner_id is not None
            and not OpportunityTeam.query.filter(
                OpportunityTeam.opportunity_id == opportunity.opportunity_id,
                OpportunityTeam.role == SOLUTION_ENGINEER,
            ).first()
        )

    @staticmethod
    def can_create_opportunity(user, active_role):
        return active_role == SALES_EXECUTIVE

    @staticmethod
    def can_update_opportunity(user, active_role, opportunity, data):
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return False

        if active_role == SALES_EXECUTIVE:
            stage = opportunity.current_stage
            return (
                opportunity.created_by == user.user_id
                and opportunity.is_active
                and opportunity.status == "Open"
                and stage is not None
                and stage.display_order <= 2
            )

        return False

    @staticmethod
    def can_delete_opportunity(user, active_role, opportunity):
        # Destructive business workflow is deliberately deferred. No ordinary
        # business role receives delete authority in Phase 2.
        return False

    @staticmethod
    def is_assigned_role(user, opportunity, role):
        return bool(
            user and opportunity and
            OpportunityTeam.query.filter_by(
                opportunity_id=opportunity.opportunity_id,
                user_id=user.user_id,
                role=role,
            ).first()
        )

    @staticmethod
    def can_edit_solution_design(user, active_role, opportunity):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(opportunity)
            and opportunity.is_active
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
            and not POCTracker.query.filter(
                POCTracker.opportunity_id == opportunity.opportunity_id,
                POCTracker.status.in_({POC_STATUS_APPROVED, POC_STATUS_IN_PROGRESS, POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED}),
            ).first()
        )

    @staticmethod
    def can_request_poc(user, active_role, opportunity):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(opportunity)
            and opportunity.is_active
            and AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and opportunity.status == "Active"
            and opportunity.current_stage is not None
            and opportunity.current_stage.stage_name in {
                "Discovery", "POC / Technical Evaluation"
            }
        )

    @staticmethod
    def can_approve_poc(user, active_role, poc):
        return False

    @staticmethod
    def can_execute_poc(user, active_role, poc):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(poc)
            and poc.status in {POC_STATUS_APPROVED, POC_STATUS_IN_PROGRESS}
            and poc.opportunity is not None
            and poc.opportunity.is_active
            and AuthorizationService.is_assigned_role(user, poc.opportunity, SOLUTION_ENGINEER)
            and AuthorizationService.can_view_opportunity(user, active_role, poc.opportunity)
        )

    @staticmethod
    def can_edit_poc_design(user, active_role, poc):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(poc)
            and poc.status in {POC_STATUS_DRAFT, POC_STATUS_APPROVED}
            and poc.opportunity is not None
            and poc.opportunity.is_active
            and AuthorizationService.is_assigned_role(user, poc.opportunity, SOLUTION_ENGINEER)
            and AuthorizationService.can_view_opportunity(user, active_role, poc.opportunity)
        )

    @staticmethod
    def can_complete_poc(user, active_role, poc):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(poc)
            and poc.status == POC_STATUS_SUBMITTED
            and poc.opportunity is not None
            and poc.opportunity.is_active
            and AuthorizationService.is_assigned_role(user, poc.opportunity, SOLUTION_ENGINEER)
            and AuthorizationService.can_view_opportunity(user, active_role, poc.opportunity)
        )

    @staticmethod
    def can_change_technical_stage(user, active_role, opportunity):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(opportunity)
            and opportunity.is_active
            and AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
        )

    @staticmethod
    def can_close_opportunity(user, active_role, opportunity):
        return AuthorizationService.can_change_technical_stage(user, active_role, opportunity)

    @staticmethod
    def can_mutate_related(user, active_role, opportunity, resource, action):
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return False

        if resource == Resources.STAKEHOLDER:
            if active_role != SOLUTION_ENGINEER:
                return False
            return (
                opportunity.is_active
                and AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
                and opportunity.current_stage is not None
                and opportunity.current_stage.display_order >= 3
            )

        if resource == Resources.POC:
            # POC mutation is only available through explicit Phase 6 actions.
            return False

        return False


def active_role_required(fn):
    """Require a valid JWT active role and verify it still belongs to the user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            AuthorizationService.current_context()
        except AuthorizationDenied as exc:
            message = str(exc)
            status = 401 if "stale" in message.lower() else 403
            return jsonify({"message": message}), status
        return fn(*args, **kwargs)

    return wrapper


def phase2_auth_required(fn):
    """JWT authentication + server-side active-role validation."""
    decorated = active_role_required(fn)
    return jwt_required()(decorated)

def business_access_required(fn):
    """JWT authentication + active role validation + Admin business denial."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            _, active_role = AuthorizationService.current_context()
        except AuthorizationDenied as exc:
            message = str(exc)
            status = 401 if "stale" in message.lower() else 403
            return jsonify({"message": message}), status
        if active_role == ADMIN:
            return jsonify({"message": "Admin business-data access is not permitted."}), 403
        return fn(*args, **kwargs)

    return jwt_required()(wrapper)

