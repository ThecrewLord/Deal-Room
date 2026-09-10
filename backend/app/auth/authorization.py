from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import exists, or_, false

from app.constants.auth_constants import (
    STATUS_APPROVED,
    STATUS_REVOKED,
)

from app.constants.roles import (
    ADMIN,
    DATA_ANALYST,
    DELIVERY,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
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
from app.models.opportunity.stage_master import StageMaster
from app.models.delivery.delivery_project import DeliveryProject
from app.models.system.audit_log import AuditLog

from app.constants.poc_outcome import (
    POC_STATUS_DRAFT,
    POC_STATUS_IN_PROGRESS,
    POC_STATUS_SUBMITTED,
    POC_STATUS_COMPLETED,
)


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
    """
    Central Phase-2 authorization and visibility policy layer.

    Phase 9 security requirement:
    --------------------------------
    JWTs contain an auth_version.

    When an administrator changes a user's roles, manager, or access,
    the user's database auth_version is incremented.

    Therefore:

        JWT auth_version != database auth_version
                         ↓
                  session is stale
                         ↓
                        401
    """

    IC_ROLES = {
        SALES_EXECUTIVE,
        SOLUTION_ENGINEER,
    }

    # ================================================================
    # CURRENT AUTHENTICATION CONTEXT
    # ================================================================

    @staticmethod
    def current_context():
        """
        Validate the authenticated user's current authorization state.

        The auth_version stored in the JWT must exactly match the
        auth_version currently stored in the database.

        Any administrator action that changes roles, manager assignment,
        approval, or revocation increments auth_version. Therefore an
        older JWT immediately becomes invalid.
        """

        claims = get_jwt()
        identity = get_jwt_identity()

        # ------------------------------------------------------------
        # Parse user identity.
        # ------------------------------------------------------------

        try:
            user_id = int(identity)
        except (TypeError, ValueError):
            raise AuthorizationDenied(
                "Invalid authenticated user."
            )

        # ------------------------------------------------------------
        # IMPORTANT:
        #
        # Clear SQLAlchemy's identity-map cache before checking the
        # authorization version.
        #
        # This guarantees that the value comes from the database rather
        # than from an already-loaded User object.
        # ------------------------------------------------------------

        db.session.expire_all()

        database_version = (
            db.session.execute(
                db.select(User.auth_version).where(
                    User.user_id == user_id
                )
            )
            .scalar_one_or_none()
        )

        user = (
            db.session.query(User)
            .populate_existing()
            .filter(
                User.user_id == user_id
            )
            .first()
        )

        claims_version = claims.get("auth_version")
        active_role = normalize_role(
            claims.get("active_role")
        )

        # ------------------------------------------------------------
        # User existence.
        # ------------------------------------------------------------

        if not user:
            raise AuthorizationDenied(
                "Authenticated user is not active."
            )

        # ------------------------------------------------------------
        # Revoked users.
        # ------------------------------------------------------------

        if user.status == STATUS_REVOKED:
            raise AuthorizationDenied(
                "Your access has been revoked."
            )

        # ------------------------------------------------------------
        # Only approved + active users are valid.
        # ------------------------------------------------------------

        if (
            not user.active
            or user.status != STATUS_APPROVED
        ):
            raise AuthorizationDenied(
                "Authenticated user is not active."
            )

        # ------------------------------------------------------------
        # auth_version must exist in the JWT.
        #
        # This also rejects legacy tokens issued before Phase 9.
        # ------------------------------------------------------------

        if claims_version is None:
            raise AuthorizationDenied(
                "Session is stale. Please sign in again."
            )

        # ------------------------------------------------------------
        # Convert both values to integers.
        # ------------------------------------------------------------

        try:
            token_version = int(claims_version)

            if database_version is None:
                raise ValueError

            database_version = int(database_version)

        except (TypeError, ValueError):
            raise AuthorizationDenied(
                "Session is stale. Please sign in again."
            )

        # ------------------------------------------------------------
        # PHASE 9 CORE SECURITY CHECK
        #
        # Old JWT:
        #     auth_version = 1
        #
        # Database after admin role change:
        #     auth_version = 2
        #
        # Result:
        #     401 Session is stale.
        # ------------------------------------------------------------

        if token_version != database_version:
            raise AuthorizationDenied(
                "Session is stale. Please sign in again."
            )

        # ------------------------------------------------------------
        # Active role must still be valid.
        # ------------------------------------------------------------

        if not is_valid_role(active_role):
            raise AuthorizationDenied(
                "A valid active role is required."
            )

        # ------------------------------------------------------------
        # Active role must still belong to the user.
        # ------------------------------------------------------------

        if not user.has_role(active_role):
            raise AuthorizationDenied(
                "Active role is no longer assigned to this user."
            )

        # ------------------------------------------------------------
        # Store authoritative authorization context.
        # ------------------------------------------------------------

        g.auth_user = user
        g.active_role = active_role

        return user, active_role

    # ================================================================
    # OPPORTUNITY VISIBILITY
    # ================================================================

    @staticmethod
    def opportunity_query(user, active_role):
        """
        Return only opportunities visible to the active role.
        """

        query = Opportunity.query

        # Admins do not receive business opportunity data.
        if active_role == ADMIN:
            return query.filter(false())

        # ------------------------------------------------------------
        # Individual contributors:
        # only opportunities where they are explicitly assigned.
        # ------------------------------------------------------------

        participation = exists().where(
            (
                OpportunityTeam.opportunity_id
                == Opportunity.opportunity_id
            )
            & (
                OpportunityTeam.user_id
                == user.user_id
            )
            & (
                OpportunityTeam.role
                == active_role
            )
        )

        if active_role in AuthorizationService.IC_ROLES:
            return query.filter(
                participation
            )

        # ------------------------------------------------------------
        # Delivery visibility.
        # ------------------------------------------------------------

        if active_role == DELIVERY:
            return query.filter(participation)

        # ------------------------------------------------------------
        # Sales Manager visibility.
        # ------------------------------------------------------------

        if active_role == SALES_MANAGER:

            sales_team = exists().where(
                (
                    OpportunityTeam.opportunity_id
                    == Opportunity.opportunity_id
                )
                & (
                    OpportunityTeam.role
                    == SALES_EXECUTIVE
                )
            )

            assigned_sales_owner = (
                Opportunity.sales_owner_id.isnot(None)
            )

            pre_handoff = exists().where(
                (
                    StageMaster.stage_id
                    == Opportunity.stage_id
                )
                & (
                    StageMaster.display_order
                    <= 2
                )
            ).correlate_except(
                StageMaster
            )

            return query.filter(
                or_(
                    sales_team,
                    assigned_sales_owner,
                    pre_handoff,
                )
            )

        # ------------------------------------------------------------
        # Pre-Sales Manager visibility.
        # ------------------------------------------------------------

        if active_role == PRE_SALES_MANAGER:

            technical_team = exists().where(
                (
                    OpportunityTeam.opportunity_id
                    == Opportunity.opportunity_id
                )
                & (
                    OpportunityTeam.role
                    == SOLUTION_ENGINEER
                )
            )

            pre_sales_stage = exists().where(
                (
                    StageMaster.stage_id
                    == Opportunity.stage_id
                )
                & (
                    StageMaster.display_order
                    >= 3
                )
            ).correlate_except(
                StageMaster
            )

            awaiting_assignment = (
                (
                    Opportunity.status
                    == "Approved"
                )
                & Opportunity.sales_owner_id.isnot(None)
                & ~exists().where(
                    (
                        OpportunityTeam.opportunity_id
                        == Opportunity.opportunity_id
                    )
                    & (
                        OpportunityTeam.role
                        == SOLUTION_ENGINEER
                    )
                )
            )

            return query.filter(
                or_(
                    technical_team,
                    pre_sales_stage,
                    awaiting_assignment,
                )
            )

        return query.filter(false())

    # ================================================================
    # OPPORTUNITY ACCESS
    # ================================================================

    @staticmethod
    def can_view_opportunity(
        user,
        active_role,
        opportunity,
    ):
        if not opportunity:
            return False

        return (
            AuthorizationService.opportunity_query(
                user,
                active_role,
            )
            .filter(
                Opportunity.opportunity_id
                == opportunity.opportunity_id
            )
            .first()
            is not None
        )

    # ================================================================
    # ACCOUNT VISIBILITY
    # ================================================================

    @staticmethod
    def account_query(
        user,
        active_role,
    ):
        """
        Accounts are visible only when at least one visible opportunity
        belongs to that account.

        Seeing an Account therefore does NOT automatically grant access
        to every opportunity belonging to that account.
        """

        if active_role == ADMIN:
            return Account.query.filter(
                false()
            )

        visible_opportunities = (
            AuthorizationService.opportunity_query(
                user,
                active_role,
            )
            .with_entities(
                Opportunity.account_id
            )
            .subquery()
        )

        return Account.query.filter(
            Account.account_id.in_(
                visible_opportunities
            )
        )

    @staticmethod
    def can_view_account(
        user,
        active_role,
        account,
    ):
        return (
            bool(account)
            and AuthorizationService.account_query(
                user,
                active_role,
            )
            .filter(
                Account.account_id
                == account.account_id
            )
            .first()
            is not None
        )

    # ================================================================
    # STAKEHOLDER VISIBILITY
    # ================================================================

    @staticmethod
    def can_view_stakeholder(
        user,
        active_role,
        stakeholder,
    ):
        return (
            bool(stakeholder)
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                stakeholder.opportunity,
            )
        )

    # ================================================================
    # POC VISIBILITY
    # ================================================================

    @staticmethod
    def can_view_poc(
        user,
        active_role,
        poc,
    ):
        return (
            bool(poc)
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                poc.opportunity,
            )
        )

    # ================================================================
    # OEM VISIBILITY
    # ================================================================

    @staticmethod
    def can_view_oem(
        user,
        active_role,
        oem,
    ):
        return (
            bool(oem)
            and AuthorizationService.account_query(
                user,
                active_role,
            )
            .filter(
                Account.account_id
                == oem.account_id
            )
            .first()
            is not None
        )

    @staticmethod
    def can_manage_oem(
        user,
        active_role,
        oem=None,
    ):
        if active_role not in {
            SALES_MANAGER,
            PRE_SALES_MANAGER,
        }:
            return False

        if oem is None:
            return True

        return AuthorizationService.can_view_oem(
            user,
            active_role,
            oem,
        )

    # ================================================================
    # ACTIVITY VISIBILITY
    # ================================================================

    @staticmethod
    def can_view_activity(
        user,
        active_role,
        entity_type,
        entity_id,
    ):
        # Admin can only view administrative audit activity.
        if active_role == ADMIN:
            return (
                entity_type.lower()
                in {
                    "admin",
                    "user",
                    "access",
                }
            )

        # ------------------------------------------------------------
        # Opportunity activity.
        # ------------------------------------------------------------

        if entity_type.lower() == "opportunity":

            opportunity = Opportunity.query.get(
                entity_id
            )

            return AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )

        # ------------------------------------------------------------
        # Account activity.
        # ------------------------------------------------------------

        if entity_type.lower() == "account":

            account = Account.query.get(
                entity_id
            )

            return AuthorizationService.can_view_account(
                user,
                active_role,
                account,
            )

        # ------------------------------------------------------------
        # Stakeholder activity.
        # ------------------------------------------------------------

        if entity_type.lower() == "stakeholder":

            stakeholder = Stakeholder.query.get(
                entity_id
            )

            return AuthorizationService.can_view_stakeholder(
                user,
                active_role,
                stakeholder,
            )

        # ------------------------------------------------------------
        # POC activity.
        # ------------------------------------------------------------

        if entity_type.lower() in {
            "poc",
            "poctracker",
        }:

            poc = POCTracker.query.get(
                entity_id
            )

            return AuthorizationService.can_view_poc(
                user,
                active_role,
                poc,
            )

        return False

    # ================================================================
    # OPPORTUNITY QUALIFICATION
    # ================================================================

    @staticmethod
    def can_qualify_opportunity(
        user,
        active_role,
        opportunity,
    ):
        return (
            active_role == SALES_EXECUTIVE
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )
            and opportunity.created_by
            == user.user_id
            and opportunity.is_active
            and opportunity.status
            == "Open"
            and opportunity.current_stage
            is not None
            and opportunity.current_stage.stage_name
            == "Lead / Identified"
        )

    # ================================================================
    # SUBMIT FOR REVIEW
    # ================================================================

    @staticmethod
    def can_submit_for_review(
        user,
        active_role,
        opportunity,
    ):
        return (
            active_role == SALES_EXECUTIVE
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )
            and opportunity.created_by
            == user.user_id
            and opportunity.is_active
            and opportunity.status
            == "Open"
            and opportunity.current_stage
            is not None
            and opportunity.current_stage.stage_name
            == "Qualification"
        )

    # ================================================================
    # SALES MANAGER REVIEW
    # ================================================================

    @staticmethod
    def can_view_pending_review(
        user,
        active_role,
    ):
        return (
            active_role
            == SALES_MANAGER
        )

    @staticmethod
    def can_review_opportunity(
        user,
        active_role,
        opportunity,
    ):
        return (
            active_role == SALES_MANAGER
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )
            and opportunity.is_active
            and opportunity.status
            == "Pending Sales Manager Review"
        )

    @staticmethod
    def can_approve_opportunity(
        user,
        active_role,
        opportunity,
    ):
        return AuthorizationService.can_review_opportunity(
            user,
            active_role,
            opportunity,
        )

    @staticmethod
    def can_reject_opportunity(
        user,
        active_role,
        opportunity,
    ):
        return AuthorizationService.can_review_opportunity(
            user,
            active_role,
            opportunity,
        )

    # ================================================================
    # SALES OWNER ASSIGNMENT
    # ================================================================

    @staticmethod
    def can_assign_sales_owner(
        user,
        active_role,
        opportunity,
        sales_owner,
    ):
        return (
            AuthorizationService.can_approve_opportunity(
                user,
                active_role,
                opportunity,
            )
            and bool(sales_owner)
            and sales_owner.active
            and sales_owner.status
            == STATUS_APPROVED
            and sales_owner.has_role(
                SALES_EXECUTIVE
            )
        )

    @staticmethod
    def can_reassign_sales_owner(
        user,
        active_role,
        opportunity,
    ):
        return False

    # ================================================================
    # PRE-SALES ASSIGNMENT
    # ================================================================

    @staticmethod
    def can_view_pending_pre_sales_assignment(
        user,
        active_role,
    ):
        return (
            active_role
            == PRE_SALES_MANAGER
        )

    @staticmethod
    def can_finalize_pre_sales_assignment(
        user,
        active_role,
        opportunity,
    ):
        return (
            active_role
            == PRE_SALES_MANAGER
            and bool(opportunity)
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )
            and opportunity.is_active
            and opportunity.status
            == "Approved"
            and opportunity.sales_owner_id
            is not None
            and not OpportunityTeam.query.filter(
                OpportunityTeam.opportunity_id
                == opportunity.opportunity_id,
                OpportunityTeam.role
                == SOLUTION_ENGINEER,
            ).first()
        )

    # ================================================================
    # OPPORTUNITY CREATION
    # ================================================================

    @staticmethod
    def can_create_opportunity(
        user,
        active_role,
    ):
        return (
            active_role
            == SALES_EXECUTIVE
        )

    # ================================================================
    # OPPORTUNITY UPDATE
    # ================================================================

    @staticmethod
    def can_update_opportunity(
        user,
        active_role,
        opportunity,
        data,
    ):
        if not AuthorizationService.can_view_opportunity(
            user,
            active_role,
            opportunity,
        ):
            return False

        if active_role == SALES_EXECUTIVE:

            stage = opportunity.current_stage

            return (
                opportunity.created_by
                == user.user_id
                and opportunity.is_active
                and opportunity.status
                == "Open"
                and stage is not None
                and stage.display_order
                <= 2
            )

        return False

    # ================================================================
    # OPPORTUNITY DELETE
    # ================================================================

    @staticmethod
    def can_delete_opportunity(
        user,
        active_role,
        opportunity,
    ):
        return False

    # ================================================================
    # OPPORTUNITY TEAM
    # ================================================================

    @staticmethod
    def is_assigned_role(
        user,
        opportunity,
        role,
    ):
        return bool(
            user
            and opportunity
            and OpportunityTeam.query.filter_by(
                opportunity_id=(
                    opportunity.opportunity_id
                ),
                user_id=user.user_id,
                role=role,
            ).first()
        )

    # ================================================================
    # SOLUTION DESIGN
    # ================================================================

    @staticmethod
    def can_edit_solution_design(
        user,
        active_role,
        opportunity,
    ):
        return (
            active_role
            == SOLUTION_ENGINEER
            and bool(opportunity)
            and opportunity.is_active
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )
            and AuthorizationService.is_assigned_role(
                user,
                opportunity,
                SOLUTION_ENGINEER,
            )
            and not POCTracker.query.filter(
                POCTracker.opportunity_id
                == opportunity.opportunity_id,
                POCTracker.status.in_(
                    {
                        POC_STATUS_DRAFT,
                        POC_STATUS_IN_PROGRESS,
                        POC_STATUS_SUBMITTED,
                        POC_STATUS_COMPLETED,
                    }
                ),
            ).first()
        )

    # ================================================================
    # POC REQUEST
    # ================================================================

    @staticmethod
    def can_request_poc(
        user,
        active_role,
        opportunity,
    ):
        return (
            active_role
            == SOLUTION_ENGINEER
            and bool(opportunity)
            and opportunity.is_active
            and AuthorizationService.is_assigned_role(
                user,
                opportunity,
                SOLUTION_ENGINEER,
            )
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )
            and opportunity.current_stage
            is not None
            and opportunity.current_stage.stage_name
            == "POC / Technical Evaluation"
        )

    @staticmethod
    def can_assign_poc(
        user,
        active_role,
        poc,
    ):
        return (
            active_role
            == PRE_SALES_MANAGER
            and bool(poc)
            and poc.opportunity
            is not None
            and poc.opportunity.is_active
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                poc.opportunity,
            )
        )

    # ================================================================
    # POC EXECUTION
    # ================================================================

    @staticmethod
    def can_execute_poc(
        user,
        active_role,
        poc,
    ):
        return (
            active_role
            == SOLUTION_ENGINEER
            and bool(poc)
            and poc.status
            in {
                POC_STATUS_DRAFT,
                POC_STATUS_IN_PROGRESS,
            }
            and poc.opportunity
            is not None
            and poc.opportunity.is_active
            and AuthorizationService.is_assigned_role(
                user,
                poc.opportunity,
                SOLUTION_ENGINEER,
            )
            and any(
                assignment.user_id == user.user_id
                and assignment.is_active
                for assignment in poc.assignments
            )
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                poc.opportunity,
            )
        )

    # ================================================================
    # POC DESIGN
    # ================================================================

    @staticmethod
    def can_edit_poc_design(
        user,
        active_role,
        poc,
    ):
        return (
            active_role
            == SOLUTION_ENGINEER
            and bool(poc)
            and poc.status
            == POC_STATUS_DRAFT
            and poc.opportunity
            is not None
            and poc.opportunity.is_active
            and AuthorizationService.is_assigned_role(
                user,
                poc.opportunity,
                SOLUTION_ENGINEER,
            )
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                poc.opportunity,
            )
        )

    # ================================================================
    # POC COMPLETION
    # ================================================================

    @staticmethod
    def can_complete_poc(
        user,
        active_role,
        poc,
    ):
        return (
            active_role
            == SOLUTION_ENGINEER
            and bool(poc)
            and poc.status
            == POC_STATUS_SUBMITTED
            and poc.opportunity
            is not None
            and poc.opportunity.is_active
            and AuthorizationService.is_assigned_role(
                user,
                poc.opportunity,
                SOLUTION_ENGINEER,
            )
            and any(
                assignment.user_id == user.user_id
                and assignment.is_active
                for assignment in poc.assignments
            )
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                poc.opportunity,
            )
        )

    # ================================================================
    # DELIVERY PROJECT
    # ================================================================

    @staticmethod
    def can_create_delivery_project(
        user,
        active_role,
        opportunity,
        poc,
    ):
        """
        A delivery project can only be created by an approved and active
        Delivery Manager from a completed POC belonging to the supplied
        opportunity.
        """
        if active_role != DELIVERY_MANAGER:
            return False

        if not user or not opportunity or not poc:
            return False

        if not user.active:
            return False

        if user.status != STATUS_APPROVED:
            return False

        if not opportunity.is_active:
            return False

        if poc.opportunity_id != opportunity.opportunity_id:
            return False

        return poc.status == POC_STATUS_COMPLETED

    @staticmethod
    def can_view_pending_delivery_assignments(user, active_role):
        """
        Only an approved and active Delivery Manager can view
        pending delivery assignments.
        """
        if not user:
            return False

        if not user.active:
            return False

        if user.status != STATUS_APPROVED:
            return False

        return active_role == DELIVERY_MANAGER

    @staticmethod
    def can_view_delivery_candidates(user, active_role):
        """
        Only an approved and active Delivery Manager can view
        delivery-team candidates.
        """
        if not user:
            return False

        if not user.active:
            return False

        if user.status != STATUS_APPROVED:
            return False

        return active_role == DELIVERY_MANAGER

    @staticmethod
    def can_view_delivery_project(
        user,
        active_role,
        project,
    ):
        """
        Delivery project visibility.

        Delivery Managers can view delivery projects.

        Delivery Engineers, Data Analysts, and Delivery users
        can view only projects to which they are actively assigned
        with their current active role.

        Other business roles and Admin have no delivery-project access.
        """

        if not user or not project:
            return False

        if not user.active:
            return False

        if user.status != STATUS_APPROVED:
            return False

        # ------------------------------------------------------------
        # Admin does not receive business delivery data.
        # ------------------------------------------------------------

        if active_role == ADMIN:
            return False

        # ------------------------------------------------------------
        # Delivery Manager visibility.
        #
        # A Delivery Manager is responsible for delivery projects
        # and therefore has project-level visibility.
        # ------------------------------------------------------------

        if active_role == DELIVERY_MANAGER:
            return True

        # ------------------------------------------------------------
        # Delivery team visibility.
        #
        # The user must have an active assignment to this project
        # using the currently selected active role.
        # ------------------------------------------------------------

        if active_role not in {
            DEVOPS_ENGINEER,
            DATA_ANALYST,
            DELIVERY,
        }:
            return False

        return any(
            assignment.user_id == user.user_id
            and assignment.is_active
            and assignment.role == active_role
            for assignment in project.assignments
        )
        if active_role != DELIVERY_MANAGER:
            return False

        if not user or not opportunity or not poc:
            return False

        if not user.active:
            return False

        if user.status != STATUS_APPROVED:
            return False

        if not opportunity.is_active:
            return False

        if poc.opportunity_id != opportunity.opportunity_id:
            return False

        return poc.status == POC_STATUS_COMPLETED

    # ================================================================
    # TECHNICAL STAGE CHANGE
    # ================================================================

    @staticmethod
    def can_change_technical_stage(
        user,
        active_role,
        opportunity,
    ):
        return (
            active_role
            == SOLUTION_ENGINEER
            and bool(opportunity)
            and opportunity.is_active
            and AuthorizationService.is_assigned_role(
                user,
                opportunity,
                SOLUTION_ENGINEER,
            )
            and AuthorizationService.can_view_opportunity(
                user,
                active_role,
                opportunity,
            )
        )

    # ================================================================
    # CLOSE OPPORTUNITY
    # ================================================================

    @staticmethod
    def can_close_opportunity(
        user,
        active_role,
        opportunity,
    ):
        return AuthorizationService.can_change_technical_stage(
            user,
            active_role,
            opportunity,
        )

    # ================================================================
    # RELATED RESOURCE MUTATION
    # ================================================================

    @staticmethod
    def can_mutate_related(
        user,
        active_role,
        opportunity,
        resource,
        action,
    ):
        if not AuthorizationService.can_view_opportunity(
            user,
            active_role,
            opportunity,
        ):
            return False

        # ------------------------------------------------------------
        # Stakeholders.
        # ------------------------------------------------------------

        if resource == Resources.STAKEHOLDER:

            if active_role == SALES_EXECUTIVE:
                required_role = SALES_EXECUTIVE

            elif active_role == SOLUTION_ENGINEER:
                required_role = SOLUTION_ENGINEER

            else:
                return False

            return (
                opportunity.is_active
                and AuthorizationService.is_assigned_role(
                    user,
                    opportunity,
                    required_role,
                )
            )

        # ------------------------------------------------------------
        # POC.
        # ------------------------------------------------------------

        if resource == Resources.POC:
            return False

        return False


# ====================================================================
# AUTHORIZATION DECORATORS
# ====================================================================

def active_role_required(fn):
    """
    Require a valid JWT active role and verify that the role,
    user status and auth_version still belong to the user.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):

        try:
            AuthorizationService.current_context()

        except AuthorizationDenied as exc:

            message = str(exc)

            # A stale session must be returned as 401.
            status = (
                401
                if "stale"
                in message.lower()
                else 403
            )

            return jsonify({
                "message": message
            }), status

        return fn(*args, **kwargs)

    return wrapper


def phase2_auth_required(fn):
    """
    JWT authentication plus server-side authorization validation.

    This is used for endpoints such as /api/auth/me.

    Important Phase 9 behavior:

        Existing JWT
              ↓
        auth_version = 1
              ↓
        admin changes role
              ↓
        database auth_version = 2
              ↓
        /api/auth/me
              ↓
        401 Session is stale
    """

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):

        try:
            AuthorizationService.current_context()

        except AuthorizationDenied as exc:

            message = str(exc)

            status = (
                401
                if "stale"
                in message.lower()
                else 403
            )

            return jsonify({
                "message": message
            }), status

        return fn(*args, **kwargs)

    return wrapper


def business_access_required(fn):
    """
    JWT authentication + active-role validation +
    Admin business-data denial.
    """

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):

        try:
            _, active_role = (
                AuthorizationService.current_context()
            )

        except AuthorizationDenied as exc:

            message = str(exc)

            status = (
                401
                if "stale"
                in message.lower()
                else 403
            )

            return jsonify({
                "message": message
            }), status

        # Admin accounts are intentionally prevented from
        # accessing normal business data through these routes.
        if active_role == ADMIN:

            return jsonify({
                "message": (
                    "Admin business-data access "
                    "is not permitted."
                )
            }), 403

        return fn(*args, **kwargs)

    return wrapper