from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import exists, or_, false

from app.constants.auth_constants import STATUS_APPROVED, STATUS_REVOKED
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
    is_valid_role,
)
from app.database import db
from app.models.account.account import Account
from app.models.account.oem_partner import OEMPartner
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.repositories.auth_repository import AuthRepository
from app.constants.system_permissions import MANAGE_ADMINS
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stakeholder import Stakeholder
from app.models.system.audit_log import AuditLog
from app.models.phase2 import DeliveryProject, DeliveryProjectMember, Activity, FollowUp, POCTeamMember, OEMOpportunity, RFXContext, NegotiationContext
from app.models.opportunity.stage_master import StageMaster
from app.constants.poc_outcome import (POC_STATUS_DRAFT, POC_STATUS_IN_PROGRESS, POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED)


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
    FOLLOW_UP = "follow_up"
    DELIVERY_PROJECT = "delivery_project"


class AuthorizationService:
    """Central Phase-2 authorization and visibility policy layer."""

    IC_ROLES = {SALES_EXECUTIVE, SOLUTION_ENGINEER}

    @staticmethod
    def current_context():
        """Build the authoritative request authorization context.

        The JWT supplies identity and the selected active role, but every
        security-sensitive fact is reloaded from the database.
        """
        claims = get_jwt()
        identity = get_jwt_identity()

        try:
            user_id = int(identity)
        except (TypeError, ValueError):
            raise AuthorizationDenied("Invalid authenticated user.")

        user = User.query.filter_by(user_id=user_id).first()
        active_role = claims.get("active_role")
        claims_version = claims.get("auth_version")

        if not user:
            raise AuthorizationDenied("Authenticated user is not active.")
        if user.status == STATUS_REVOKED:
            raise AuthorizationDenied("Your access has been revoked.")
        if not user.active or user.status != STATUS_APPROVED:
            raise AuthorizationDenied("Authenticated user is not active.")
        try:
            version_matches = claims_version is not None and int(claims_version) == int(user.auth_version)
        except (TypeError, ValueError):
            version_matches = False
        if not version_matches:
            raise AuthorizationDenied("Session is stale. Please sign in again.")
        if not is_valid_role(active_role):
            raise AuthorizationDenied("A valid active role is required.")
        if not user.has_role(active_role):
            raise AuthorizationDenied("Active role is no longer assigned to this user.")

        g.auth_user = user
        g.active_role = active_role
        return user, active_role

    @staticmethod
    def is_leadership(user, active_role):
        return bool(user and active_role == LEADERSHIP and user.has_role(LEADERSHIP))

    @staticmethod
    def has_delegated_admin_capability(user, active_role):
        return bool(
            user
            and active_role == ADMIN
            and user.has_role(ADMIN)
            and AuthRepository.has_system_permission(user.user_id, MANAGE_ADMINS)
        )

    @staticmethod
    def can_manage_system(user, active_role):
        # The Admin role itself represents delegated system administration.
        # MANAGE_ADMINS is the narrower capability required to delegate the
        # Admin role onward.
        return bool(
            user
            and ((active_role == LEADERSHIP and user.has_role(LEADERSHIP))
                 or (active_role == ADMIN and user.has_role(ADMIN)))
        )

    @staticmethod
    def can_view_admin_identities(user, active_role):
        return AuthorizationService.is_leadership(user, active_role)

    @staticmethod
    def can_assign_role(user, active_role, target, role):
        if not target or not is_valid_role(role):
            return False
        if active_role == LEADERSHIP:
            return True
        if active_role != ADMIN:
            return False
        # Leadership assignment is always reserved to Leadership.
        if role == LEADERSHIP:
            return False
        # Admin assignment is a separately delegable capability.
        if role == ADMIN:
            return AuthorizationService.has_delegated_admin_capability(user, active_role) and not target.has_role(LEADERSHIP) and not target.has_role(ADMIN)
        if target.has_role(LEADERSHIP) or target.has_role(ADMIN):
            return False
        return True

    @staticmethod
    def can_manage_target_roles(user, active_role, target):
        if not target:
            return False
        if active_role == LEADERSHIP:
            return True
        if active_role == ADMIN:
            return not target.has_role(LEADERSHIP) and not target.has_role(ADMIN)
        return False

    @staticmethod
    def can_revoke_user(user, active_role, target):
        if not target or target.user_id == user.user_id:
            return False
        if active_role == LEADERSHIP:
            return True
        # Delegated Admins may administer ordinary users only. Privileged
        # identities remain Leadership-governed and cannot be touched here.
        return active_role == ADMIN and not target.has_role(LEADERSHIP) and not target.has_role(ADMIN)

    @staticmethod
    def can_change_manager(user, active_role, target):
        if not target:
            return False
        if active_role == LEADERSHIP:
            return True
        return active_role == ADMIN and not target.has_role(LEADERSHIP) and not target.has_role(ADMIN)

    @staticmethod
    def opportunity_query(user, active_role):
        """Return only opportunities visible to the active role."""
        query = Opportunity.query

        if active_role == LEADERSHIP:
            return query
        if active_role == ADMIN:
            return query.filter(false())

        participation = exists().where(
            (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
            & (OpportunityTeam.user_id == user.user_id)
            & (OpportunityTeam.role == active_role)
        )

        own_lead = (
            (Opportunity.created_by == user.user_id)
            & exists().where(
                (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
                & (OpportunityTeam.user_id == user.user_id)
                & (OpportunityTeam.role == active_role)
            )
            & (Opportunity.lifecycle_stage == "Lead")
        )

        if active_role in AuthorizationService.IC_ROLES:
            return query.filter(or_(participation, own_lead))

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
            pre_handoff = Opportunity.lifecycle_stage.in_(["Lead", "Qualified"])
            return query.filter(or_(sales_team, assigned_sales_owner, pre_handoff, own_lead))

        if active_role == PRE_SALES_MANAGER:
            # Pre-Sales scope begins at RFX and is also retained for
            # opportunities explicitly carrying technical/delivery members.
            technical_team = exists().where(
                (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
                & (OpportunityTeam.role == SOLUTION_ENGINEER)
            )
            pre_sales_stage = Opportunity.lifecycle_stage.in_(["RFX", "POC", "Negotiations", "Delivery"])
            # Approved opportunities awaiting technical allocation are in
            # Pre-Sales scope even when their lifecycle is still Qualified.
            awaiting_assignment = (
                (Opportunity.operational_status == "Active")
                & (Opportunity.review_status == "Approved")
                & Opportunity.sales_owner_id.isnot(None)
                & ~exists().where(
                    (OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
                    & (OpportunityTeam.role == SOLUTION_ENGINEER)
                )
            )
            return query.filter(or_(technical_team, pre_sales_stage, awaiting_assignment, own_lead))

        # Delivery Manager / DevOps / Data Analyst see opportunities they
        # participate in, plus their own draft Lead.
        if active_role in {DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST}:
            return query.filter(or_(participation, own_lead))

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
        if active_role == LEADERSHIP:
            return Account.query
        if active_role == ADMIN:
            return Account.query.filter(false())
        # Frozen v2: every approved active business role may search/view the
        # canonical account directory. Account visibility is not inferred from
        # opportunity visibility because Deal Finder creation must be able to
        # select an existing canonical account before the opportunity exists.
        return Account.query

    @staticmethod
    def can_create_account(user, active_role):
        return bool(user and active_role != ADMIN and user.status == STATUS_APPROVED and user.active)

    @staticmethod
    def can_govern_account(user, active_role, account):
        return bool(user and account and active_role == LEADERSHIP and user.has_role(LEADERSHIP))

    @staticmethod
    def can_mutate_oem_master(user, active_role):
        return bool(user and active_role == LEADERSHIP and user.has_role(LEADERSHIP))

    @staticmethod
    def can_manage_oem_association(user, active_role, opportunity, action="update"):
        if not opportunity or opportunity.operational_status == "Closed":
            return False
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return False
        if opportunity.lifecycle_stage == "Lead":
            return opportunity.created_by == user.user_id and active_role in {LEADERSHIP, SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST}
        if opportunity.lifecycle_stage in {"Qualified"}:
            return active_role in {SALES_MANAGER, PRE_SALES_MANAGER, LEADERSHIP}
        return active_role in {PRE_SALES_MANAGER, SOLUTION_ENGINEER, LEADERSHIP}

    @staticmethod
    def can_manage_rfx(user, active_role, opportunity):
        return bool(opportunity and opportunity.operational_status != "Closed" and
                    AuthorizationService.can_view_opportunity(user, active_role, opportunity) and
                    active_role in {PRE_SALES_MANAGER, SOLUTION_ENGINEER, LEADERSHIP})

    @staticmethod
    def can_manage_negotiation(user, active_role, opportunity):
        return bool(opportunity and opportunity.operational_status != "Closed" and
                    AuthorizationService.can_view_opportunity(user, active_role, opportunity) and
                    active_role in {PRE_SALES_MANAGER, SOLUTION_ENGINEER, LEADERSHIP})

    @staticmethod
    def can_request_poc_team_assignment(user, active_role, poc):
        # Delivery Manager receives the POC assignment before becoming a member
        # of the Opportunity/POC team. Requiring Opportunity visibility here
        # creates a circular dependency: the manager cannot be assigned because
        # they are not yet assigned. Authorize against the POC resource itself.
        return bool(
            poc and poc.opportunity
            and poc.opportunity.operational_status != "Closed"
            and poc.opportunity.lifecycle_stage == "POC"
            and active_role in {DELIVERY_MANAGER, LEADERSHIP}
            and user and user.active
            and user.status == "APPROVED"
        )

    @staticmethod
    def can_submit_poc_result(user, active_role, poc):
        return bool(poc and poc.opportunity and poc.opportunity.operational_status != "Closed" and
                    active_role in {DEVOPS_ENGINEER, DATA_ANALYST} and
                    POCTeamMember.query.filter_by(poc_id=poc.poc_id, user_id=user.user_id).first() is not None)

    @staticmethod
    def can_manage_delivery_project(user, active_role, project):
        return bool(project and active_role in {DELIVERY_MANAGER, LEADERSHIP} and
                    AuthorizationService.can_view_opportunity(user, active_role, project.opportunity))

    @staticmethod
    def can_update_project_member_done(user, active_role, member):
        return bool(member and member.user_id == user.user_id and
                    member.project and member.project.status == "Active" and
                    AuthorizationService.can_view_opportunity(user, active_role, member.project.opportunity))

    @staticmethod
    def can_create_activity(user, active_role, opportunity):
        return bool(opportunity and opportunity.operational_status != "Closed" and
                    AuthorizationService.can_view_opportunity(user, active_role, opportunity))

    @staticmethod
    def can_manage_followup(user, active_role, followup, opportunity=None):
        opportunity = opportunity or (followup.opportunity if followup else None)
        if not opportunity or opportunity.operational_status == "Closed":
            return False
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return False
        if followup is None:
            return True
        return followup.owner_id == user.user_id or followup.created_by == user.user_id or active_role in {SALES_MANAGER, PRE_SALES_MANAGER, DELIVERY_MANAGER, LEADERSHIP}

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
        # Compatibility only: v2 qualification occurs through Lead approval.
        return False

    @staticmethod
    def can_submit_for_review(user, active_role, opportunity):
        return (
            active_role in {SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST, LEADERSHIP}
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and opportunity.created_by == user.user_id
            and opportunity.operational_status != "Closed"
            and opportunity.outcome == "Open"
            and getattr(opportunity, "lifecycle_stage", None) == "Lead"
        )

    @staticmethod
    def can_view_pending_review(user, active_role):
        return active_role in {SALES_MANAGER, LEADERSHIP}

    @staticmethod
    def can_review_opportunity(user, active_role, opportunity):
        return (
            active_role in {SALES_MANAGER, LEADERSHIP}
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and opportunity.operational_status != "Closed"
            and opportunity.lifecycle_stage == "Lead"
            and opportunity.review_status == "Pending Sales Manager Review"
        )

    @staticmethod
    def can_approve_opportunity(user, active_role, opportunity):
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
            and opportunity.operational_status == "Active"
            and opportunity.review_status == "Approved"
            and opportunity.sales_owner_id is not None
            and not OpportunityTeam.query.filter(
                OpportunityTeam.opportunity_id == opportunity.opportunity_id,
                OpportunityTeam.role == SOLUTION_ENGINEER,
            ).first()
        )

    @staticmethod
    def can_create_opportunity(user, active_role):
        # D4: every approved active role except Admin may act as Deal Finder.
        # current_context() already proves the active role is currently
        # assigned to an approved, active user.
        return bool(
            user
            and active_role in {
                LEADERSHIP, SALES_MANAGER, SALES_EXECUTIVE,
                PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER,
                DEVOPS_ENGINEER, DATA_ANALYST,
            }
            and user.has_role(active_role)
            and user.active
            and user.status == STATUS_APPROVED
        )

    @staticmethod
    def can_update_opportunity(user, active_role, opportunity, data):
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return False
        if not opportunity or opportunity.operational_status == "Closed":
            return False
        # A2 only removes lifecycle/status mutation. Ordinary field editing
        # remains governed by the existing role/domain policies.
        if active_role in {SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST}:
            return (
                opportunity.created_by == user.user_id
                and opportunity.lifecycle_stage == "Lead"
                and opportunity.review_status == "Draft"
            )
        if active_role in {SALES_MANAGER, LEADERSHIP}:
            # Initial-review editing is an explicit workflow permission, not a
            # generic business-field grant. A3 excludes Deal Finder, state,
            # Sales Owner and initial value from this path.
            if opportunity.lifecycle_stage == "Lead" and opportunity.review_status == "Pending Sales Manager Review":
                return active_role == LEADERSHIP or AuthorizationService.can_review_opportunity(user, active_role, opportunity)
            return opportunity.lifecycle_stage != "Lead" if active_role == LEADERSHIP else False
        if active_role in {PRE_SALES_MANAGER}:
            return opportunity.lifecycle_stage != "Lead"
        return False

    @staticmethod
    def can_change_opportunity_value(user, active_role, opportunity):
        """Authorize Opportunity Value changes using the active role."""
        return (
            bool(user and opportunity)
            and active_role in {
                SALES_MANAGER,
                PRE_SALES_MANAGER,
                LEADERSHIP,
            }
            and opportunity.operational_status != "Closed"
            and opportunity.outcome == "Open"
        )

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
                POCTracker.status.in_({POC_STATUS_DRAFT, POC_STATUS_IN_PROGRESS, POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED}),
            ).first()
        )

    @staticmethod
    def can_request_poc(user, active_role, opportunity):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(opportunity)
            and opportunity.is_active
            and AuthorizationService.is_assigned_role(
                user, opportunity, SOLUTION_ENGINEER
            )
            and AuthorizationService.can_view_opportunity(
                user, active_role, opportunity
            )
            and opportunity.lifecycle_stage == "POC"
        )

    @staticmethod
    def can_execute_poc(user, active_role, poc):
        assigned_poc_member = bool(poc and POCTeamMember.query.filter_by(poc_id=poc.poc_id, user_id=user.user_id).first())
        return (
            bool(poc) and poc.status in {POC_STATUS_DRAFT, POC_STATUS_IN_PROGRESS}
            and poc.opportunity is not None and poc.opportunity.is_active
            and AuthorizationService.can_view_opportunity(user, active_role, poc.opportunity)
            and (active_role == SOLUTION_ENGINEER or assigned_poc_member)
        )

    @staticmethod
    def can_edit_poc_design(user, active_role, poc):
        return (
            active_role == SOLUTION_ENGINEER
            and bool(poc)
            and poc.status == POC_STATUS_DRAFT
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
    def can_change_lifecycle_stage(user, active_role, opportunity, target_stage=None):
        if not opportunity or opportunity.operational_status == "Closed":
            return False
        if target_stage == "Delivery":
            return False  # final Closed Won approval has a dedicated action
        if opportunity.lifecycle_stage == "Lead":
            return False
        if active_role == LEADERSHIP or active_role == PRE_SALES_MANAGER:
            return True
        if active_role == SOLUTION_ENGINEER:
            return AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
        return False

    @staticmethod
    def can_change_operational_status(user, active_role, opportunity):
        return (
            bool(opportunity)
            and opportunity.operational_status != "Closed"
            and active_role in {SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, LEADERSHIP}
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
        )

    @staticmethod
    def can_close_opportunity(user, active_role, opportunity, won=False):
        # Closure is an opportunity mutation, so visibility is part of the
        # authorization decision. Never allow an otherwise-authorized role to
        # close an opportunity merely by guessing its id.
        if not opportunity or opportunity.operational_status == "Closed":
            return False
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return False
        stage = getattr(opportunity, "lifecycle_stage", None)
        if stage == "Lead":
            return active_role in {SALES_MANAGER, LEADERSHIP}
        if active_role in {PRE_SALES_MANAGER, LEADERSHIP}:
            return True
        if active_role == SOLUTION_ENGINEER:
            return (not won) and AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
        return False

    @staticmethod
    def can_request_closed_won(user, active_role, opportunity):
        return (
            bool(user and opportunity)
            and active_role == SOLUTION_ENGINEER
            and opportunity.operational_status != "Closed"
            and opportunity.outcome == "Open"
            and opportunity.lifecycle_stage in {"Qualified", "RFX", "POC", "Negotiations"}
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
            and AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
        )

    @staticmethod
    def can_approve_closed_won_request(user, active_role, opportunity):
        return (
            bool(user and opportunity)
            and active_role == PRE_SALES_MANAGER
            and opportunity.operational_status != "Closed"
            and opportunity.outcome == "Open"
            and AuthorizationService.can_view_opportunity(user, active_role, opportunity)
        )

    @staticmethod
    def can_mutate_related(user, active_role, opportunity, resource, action):
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            return False

        if resource == Resources.STAKEHOLDER:
            # Customer stakeholders are part of the commercial opportunity
            # record, so the Sales Executive who has access to the opportunity
            # may create them. Solution Engineers retain their existing
            # create permission for assigned technical opportunities.
            if active_role in {LEADERSHIP, SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST}:
                if opportunity.operational_status != "Active":
                    return False
                if active_role == SALES_EXECUTIVE:
                    if action in {"create", "set_tags"}:
                        return True
                    return False
                if opportunity.lifecycle_stage == "Lead" and opportunity.created_by == user.user_id and opportunity.review_status == "Draft":
                    return action in {"create", "set_tags", "update"}
                if active_role == SALES_MANAGER and opportunity.review_status == "Pending Sales Manager Review":
                    return action in {"create", "update", "set_tags"}
            if active_role == SOLUTION_ENGINEER:
                return (
                    opportunity.is_active
                    and AuthorizationService.is_assigned_role(user, opportunity, SOLUTION_ENGINEER)
                    and opportunity.lifecycle_stage in {"RFX", "POC", "Negotiations", "Delivery"}
                )

            return False

        if resource == Resources.POC:
            # POC mutation is only available through explicit Phase 6 actions.
            return False

        return False


def system_admin_required(fn):
    """Require Leadership or an explicitly delegated Admin capability."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            user, active_role = AuthorizationService.current_context()
        except AuthorizationDenied as exc:
            message = str(exc)
            status = 401 if "stale" in message.lower() else 403
            return jsonify({"message": message}), status
        if not AuthorizationService.can_manage_system(user, active_role):
            return jsonify({"message": "System administration access required."}), 403
        return fn(*args, **kwargs)

    return jwt_required()(wrapper)


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

