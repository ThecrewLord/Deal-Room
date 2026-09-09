from datetime import datetime, timedelta

from sqlalchemy import func

from app.auth.authorization import AuthorizationService
from app.database import db
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker
from app.models.system.audit_log import AuditLog
from app.constants.poc_outcome import POC_STATUS_DRAFT, POC_STATUS_IN_PROGRESS
from app.constants.stages import LIFECYCLE_STAGES


class DashboardRepository:
    """Read-only dashboard queries using the v2 opportunity state model.

    A2 makes lifecycle_stage/outcome/operational_status authoritative. Legacy
    stage_id/status/is_active are intentionally not used to derive dashboard
    state so the dashboard cannot regress when a lifecycle transition occurs.
    """

    @staticmethod
    def _opportunities(user, active_role):
        return AuthorizationService.opportunity_query(user, active_role)

    @staticmethod
    def _opportunity_ids(user, active_role):
        return DashboardRepository._opportunities(user, active_role).with_entities(
            Opportunity.opportunity_id
        ).subquery()

    @staticmethod
    def _open_filter(query):
        return query.filter(
            Opportunity.outcome == "Open",
            Opportunity.operational_status.in_(("Active", "Stalled")),
        )

    @staticmethod
    def get_total_opportunities(user, active_role):
        return DashboardRepository._opportunities(user, active_role).count()

    @staticmethod
    def get_total_pipeline_value(user, active_role):
        value = DashboardRepository._open_filter(
            DashboardRepository._opportunities(user, active_role)
        ).with_entities(func.sum(Opportunity.estimated_value)).scalar()
        return float(value or 0)

    @staticmethod
    def get_weighted_forecast(user, active_role):
        opportunities = DashboardRepository._open_filter(
            DashboardRepository._opportunities(user, active_role)
        ).all()
        return round(sum(
            float(o.estimated_value or 0) * (o.probability or 0) / 100
            for o in opportunities
        ), 2)

    @staticmethod
    def get_open_opportunities(user, active_role):
        return DashboardRepository._open_filter(
            DashboardRepository._opportunities(user, active_role)
        ).count()

    @staticmethod
    def get_closed_won(user, active_role):
        return DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.outcome == "Closed Won",
            Opportunity.operational_status == "Closed",
        ).count()

    @staticmethod
    def get_closed_lost(user, active_role):
        return DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.outcome == "Closed Lost",
            Opportunity.operational_status == "Closed",
        ).count()

    @staticmethod
    def get_conversion_rate(user, active_role):
        total_closed = DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.outcome.in_(("Closed Won", "Closed Lost")),
            Opportunity.operational_status == "Closed",
        ).count()
        won = DashboardRepository.get_closed_won(user, active_role)
        return 0 if total_closed == 0 else round((won / total_closed) * 100, 2)

    @staticmethod
    def _last_stage_change(opportunity):
        if opportunity.stage_history:
            return opportunity.stage_history[-1].created_at
        return opportunity.updated_at or opportunity.created_at

    @staticmethod
    def get_stage_ageing(user, active_role):
        opportunities = DashboardRepository._open_filter(
            DashboardRepository._opportunities(user, active_role)
        ).all()
        now = datetime.utcnow()
        result = []
        for opportunity in opportunities:
            changed_at = DashboardRepository._last_stage_change(opportunity)
            if changed_at:
                result.append({
                    "opportunity_id": opportunity.opportunity_id,
                    "stage": opportunity.lifecycle_stage,
                    "age_days": max(0, (now - changed_at).days),
                })
        return result

    @staticmethod
    def get_average_stage_ageing(user, active_role):
        ages = [row["age_days"] for row in DashboardRepository.get_stage_ageing(user, active_role)]
        return 0 if not ages else round(sum(ages) / len(ages), 1)

    @staticmethod
    def get_stalled_deals(user, active_role):
        limit_date = datetime.utcnow() - timedelta(days=14)
        opportunities = DashboardRepository._open_filter(
            DashboardRepository._opportunities(user, active_role)
        ).all()
        return sum(
            1 for opportunity in opportunities
            if opportunity.operational_status == "Stalled"
            or (
                DashboardRepository._last_stage_change(opportunity)
                and DashboardRepository._last_stage_change(opportunity) < limit_date
            )
        )

    @staticmethod
    def get_active_pocs(user, active_role):
        ids = DashboardRepository._opportunity_ids(user, active_role)
        return POCTracker.query.filter(
            POCTracker.opportunity_id.in_(ids),
            POCTracker.status.in_([POC_STATUS_DRAFT, POC_STATUS_IN_PROGRESS]),
        ).count()

    @staticmethod
    def get_win_loss_ratio(user, active_role):
        won = DashboardRepository.get_closed_won(user, active_role)
        lost = DashboardRepository.get_closed_lost(user, active_role)
        return won if lost == 0 else round(won / lost, 2)

    @staticmethod
    def get_partner_contribution(user, active_role):
        # No partner ownership metric exists in the current business model.
        return 0

    @staticmethod
    def get_pipeline_by_stage(user, active_role):
        """Return the frozen v2 lifecycle funnel in lifecycle order.

        StageMaster remains historical/compatibility data. Delivery has no
        legacy StageMaster row in the v2 lifecycle, so the dashboard must not
        derive the funnel from StageMaster.
        """
        rows = DashboardRepository._open_filter(
            DashboardRepository._opportunities(user, active_role)
        ).with_entities(
            Opportunity.lifecycle_stage,
            func.count(Opportunity.opportunity_id),
            func.coalesce(func.sum(Opportunity.estimated_value), 0),
        ).group_by(
            Opportunity.lifecycle_stage
        ).all()
        by_stage = {
            row[0]: {"count": row[1], "value": float(row[2] or 0)}
            for row in rows
        }
        return [
            {
                "stage": stage,
                "count": by_stage.get(stage, {}).get("count", 0),
                "value": by_stage.get(stage, {}).get("value", 0.0),
            }
            for stage in LIFECYCLE_STAGES
        ]

    @staticmethod
    def get_recent_opportunities(user, active_role, limit=5):
        opportunities = DashboardRepository._opportunities(user, active_role).order_by(
            Opportunity.updated_at.desc()
        ).limit(limit).all()
        return [
            {
                "id": o.opportunity_id,
                "name": o.opportunity_name,
                "account": o.account.account_name if o.account else "-",
                "stage": o.lifecycle_stage,
                "value": float(o.estimated_value or 0),
                "probability": o.probability or 0,
                "status": o.operational_status,
                "outcome": o.outcome,
                "updated_at": o.updated_at,
            }
            for o in opportunities
        ]

    @staticmethod
    def get_upcoming_pocs(user, active_role, limit=5):
        ids = DashboardRepository._opportunity_ids(user, active_role)
        today = datetime.utcnow().date()
        pocs = POCTracker.query.filter(
            POCTracker.opportunity_id.in_(ids),
            POCTracker.target_date >= today,
            POCTracker.status.in_([POC_STATUS_DRAFT, POC_STATUS_IN_PROGRESS]),
        ).order_by(POCTracker.target_date.asc()).limit(limit).all()
        return [
            {
                "id": p.poc_id,
                "opportunity": p.opportunity.opportunity_name if p.opportunity else "-",
                "objective": p.objective,
                "target_date": p.target_date,
                "status": p.status,
            }
            for p in pocs
        ]

    @staticmethod
    def get_recent_activity(user, active_role, limit=6):
        ids = DashboardRepository._opportunity_ids(user, active_role)
        logs = AuditLog.query.filter(
            AuditLog.entity_type.ilike("opportunity"),
            AuditLog.entity_id.in_(ids),
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        actor_ids = {log.performed_by for log in logs if log.performed_by}
        actors = {
            actor.user_id: actor.full_name
            for actor in User.query.filter(User.user_id.in_(actor_ids)).all()
        } if actor_ids else {}
        return [
            {
                "id": log.audit_log_id,
                "user": actors.get(log.performed_by, "System"),
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.description or "",
                "timestamp": log.created_at,
            }
            for log in logs
        ]
