from decimal import Decimal, InvalidOperation
import math

from sqlalchemy import update

from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.roles import LEADERSHIP, PRE_SALES_MANAGER, SALES_MANAGER, SALES_EXECUTIVE
from app.database import db
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_value_history import OpportunityValueHistory
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.services.activity_service import ActivityService
from app.services.lifecycle_transition_service import LifecycleTransitionService, TransitionConflict, TransitionInvalid


class OpportunityValueService:
    """Single authoritative mutation boundary for post-creation Opportunity Value."""

    ALLOWED_ROLES = {SALES_MANAGER, PRE_SALES_MANAGER, LEADERSHIP}

    @staticmethod
    def _validate_value(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("new_value must be a finite number.")
        try:
            value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("new_value must be a valid numeric value.")
        if not value.is_finite():
            raise ValueError("new_value must be a finite number.")
        if value < 0:
            raise ValueError("new_value must be non-negative.")
        if value.as_tuple().exponent < -2:
            raise ValueError("new_value supports at most 2 decimal places.")
        if value >= Decimal("10000000000000"):
            raise ValueError("new_value exceeds the supported precision.")
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _validate_reason(reason):
        if reason is None or not str(reason).strip():
            raise ValueError("A reason is required for every Opportunity Value change.")
        reason = str(reason).strip()
        if len(reason) > 2000:
            raise ValueError("reason must be 2000 characters or fewer.")
        return reason

    @classmethod
    def _authorize(cls, user, active_role, opportunity):
        if not AuthorizationService.can_change_opportunity_value(user, active_role, opportunity):
            raise AuthorizationDenied("This active role cannot change Opportunity Value for this opportunity.")
        LifecycleTransitionService.assert_opportunity_open_for_mutation(opportunity)

    @classmethod
    def change_value(cls, opportunity_id, new_value, reason, expected_version, user, active_role):
        new_value = cls._validate_value(new_value)
        reason = cls._validate_reason(reason)

        opportunity = Opportunity.query.filter_by(opportunity_id=opportunity_id).with_for_update().first()
        if not opportunity:
            return None

        cls._authorize(user, active_role, opportunity)
        try:
            expected = int(expected_version)
        except (TypeError, ValueError):
            raise TransitionInvalid("expected_version is required and must be an integer.")
        if expected != opportunity.row_version:
            raise TransitionConflict("Opportunity version is stale. Refresh before retrying.")

        old_value = opportunity.estimated_value
        if old_value is not None and Decimal(str(old_value)) == new_value:
            raise ValueError("new_value must be different from the current Opportunity Value.")

        try:
            result = db.session.execute(
                update(Opportunity)
                .where(
                    Opportunity.opportunity_id == opportunity.opportunity_id,
                    Opportunity.row_version == expected,
                    Opportunity.operational_status != "Closed",
                )
                .values(
                    estimated_value=new_value,
                    row_version=Opportunity.row_version + 1,
                )
            )
            if result.rowcount != 1:
                db.session.rollback()
                raise TransitionConflict("Opportunity version is stale. Refresh before retrying.")

            new_version = expected + 1
            db.session.add(OpportunityValueHistory(
                opportunity_id=opportunity.opportunity_id,
                old_value=old_value,
                new_value=new_value,
                reason=reason,
                actor_id=user.user_id,
                actor_active_role=active_role,
                opportunity_row_version=new_version,
            ))
            ActivityService.log(
                "Opportunity",
                opportunity.opportunity_id,
                "OPPORTUNITY_VALUE_CHANGED",
                f"Opportunity Value changed from {old_value} to {new_value}. Reason: {reason}",
                user.user_id,
                commit=False,
                active_role=active_role,
            )
            db.session.expire(opportunity)
            db.session.refresh(opportunity)
            db.session.commit()
        except (TransitionConflict, AuthorizationDenied, TransitionInvalid, ValueError):
            raise
        except Exception:
            db.session.rollback()
            raise
        return opportunity

    @staticmethod
    def get_history(opportunity_id, user, active_role):
        opportunity = Opportunity.query.filter_by(opportunity_id=opportunity_id).first()
        if not opportunity:
            return None
        if not AuthorizationService.can_view_opportunity(user, active_role, opportunity):
            raise AuthorizationDenied("You are not authorized to view this opportunity's value history.")
        return (
            OpportunityValueHistory.query
            .filter_by(opportunity_id=opportunity_id)
            .order_by(OpportunityValueHistory.changed_at.asc(), OpportunityValueHistory.history_id.asc())
            .all()
        )

    @staticmethod
    def record_initial_value(opportunity, user, active_role):
        """Record creation-time value without treating it as a post-creation change."""
        if opportunity.estimated_value is None:
            return
        db.session.add(OpportunityValueHistory(
            opportunity_id=opportunity.opportunity_id,
            old_value=None,
            new_value=opportunity.estimated_value,
            reason="Initial Opportunity Value",
            actor_id=user.user_id,
            actor_active_role=active_role,
            opportunity_row_version=opportunity.row_version,
        ))


class RevenueAttributionService:
    """Revenue reporting only; no incentive/commission calculation."""

    @staticmethod
    def _closed_won(query):
        return query.filter(
            Opportunity.outcome == "Closed Won",
            Opportunity.operational_status == "Closed",
            Opportunity.final_revenue.isnot(None),
        )

    @classmethod
    def for_sales_executive(cls, user, active_role):
        if active_role != SALES_EXECUTIVE:
            raise AuthorizationDenied("Revenue self-reporting is available to the active Sales Executive role only.")
        visible = AuthorizationService.opportunity_query(user, active_role)
        closed = cls._closed_won(visible).all()
        sourced = sum((Decimal(str(o.final_revenue)) for o in closed if o.created_by == user.user_id), Decimal("0"))
        participation = sum((Decimal(str(o.final_revenue)) for o in closed if OpportunityTeam.query.filter_by(
            opportunity_id=o.opportunity_id, user_id=user.user_id
        ).first()), Decimal("0"))
        return {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "sourced_revenue": float(sourced),
            "participation_revenue": float(participation),
        }

    @classmethod
    def team_report(cls, manager, active_role):
        if active_role not in {SALES_MANAGER, LEADERSHIP}:
            raise AuthorizationDenied("Only Sales Manager or Leadership can view Sales Executive revenue reporting.")
        if active_role == LEADERSHIP:
            employees = User.query.filter(
                User.active.is_(True), User.status == "APPROVED", User.roles.any(role=SALES_EXECUTIVE)
            ).order_by(User.full_name.asc()).all()
            visible = Opportunity.query
        else:
            employees = User.query.filter(
                User.manager_id == manager.user_id,
                User.active.is_(True), User.status == "APPROVED", User.roles.any(role=SALES_EXECUTIVE)
            ).order_by(User.full_name.asc()).all()
            visible = AuthorizationService.opportunity_query(manager, active_role)

        closed = cls._closed_won(visible).all()
        rows = []
        for employee in employees:
            sourced = sum((Decimal(str(o.final_revenue)) for o in closed if o.created_by == employee.user_id), Decimal("0"))
            participation = sum((Decimal(str(o.final_revenue)) for o in closed if OpportunityTeam.query.filter_by(
                opportunity_id=o.opportunity_id, user_id=employee.user_id
            ).first()), Decimal("0"))
            rows.append({
                "user_id": employee.user_id,
                "full_name": employee.full_name,
                "sourced_revenue": float(sourced),
                "participation_revenue": float(participation),
            })
        return rows
