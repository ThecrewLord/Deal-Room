from datetime import datetime, timedelta

from sqlalchemy import func

from app.auth.authorization import AuthorizationService
from app.database import db
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stage_master import StageMaster
from app.models.system.audit_log import AuditLog
from app.constants.poc_outcome import POC_STATUS_APPROVED, POC_STATUS_IN_PROGRESS


class DashboardRepository:
    @staticmethod
    def _opportunities(user, active_role):
        return AuthorizationService.opportunity_query(user, active_role)

    @staticmethod
    def _opportunity_ids(user, active_role):
        return AuthorizationService.opportunity_query(user, active_role).with_entities(
            Opportunity.opportunity_id
        ).subquery()

    @staticmethod
    def get_total_opportunities(user, active_role):
        return DashboardRepository._opportunities(user, active_role).count()

    @staticmethod
    def get_total_pipeline_value(user, active_role):
        value = DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.status.in_(["Open", "Approved", "Active"]),
            Opportunity.is_active.is_(True),
        ).with_entities(func.sum(Opportunity.estimated_value)).scalar()
        return float(value or 0)

    @staticmethod
    def get_weighted_forecast(user, active_role):
        opportunities = DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.status.in_(["Open", "Approved", "Active"]),
            Opportunity.is_active.is_(True),
        ).all()
        return round(sum(
            float(o.estimated_value or 0) * (o.probability or 0) / 100
            for o in opportunities
        ), 2)

    @staticmethod
    def get_open_opportunities(user, active_role):
        return DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.status.in_(["Open", "Approved", "Active"]),
            Opportunity.is_active.is_(True),
        ).count()

    @staticmethod
    def get_closed_won(user, active_role):
        return DashboardRepository._opportunities(user, active_role).join(StageMaster).filter(
            StageMaster.is_won.is_(True), Opportunity.is_active.is_(False)
        ).count()

    @staticmethod
    def get_closed_lost(user, active_role):
        return DashboardRepository._opportunities(user, active_role).join(StageMaster).filter(
            StageMaster.is_closed.is_(True), StageMaster.is_won.is_(False), Opportunity.is_active.is_(False)
        ).count()

    @staticmethod
    def get_conversion_rate(user, active_role):
        total_closed = DashboardRepository._opportunities(user, active_role).join(StageMaster).filter(
            StageMaster.is_closed.is_(True), Opportunity.is_active.is_(False)
        ).count()
        won = DashboardRepository._opportunities(user, active_role).join(StageMaster).filter(
            StageMaster.is_won.is_(True), Opportunity.is_active.is_(False)
        ).count()
        return 0 if total_closed == 0 else round((won / total_closed) * 100, 2)

    @staticmethod
    def _last_stage_change(opportunity):
        if opportunity.stage_history:
            return opportunity.stage_history[-1].created_at
        return opportunity.updated_at or opportunity.created_at

    @staticmethod
    def get_stage_ageing(user, active_role):
        opportunities = DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.is_active.is_(True)
        ).all()
        now = datetime.utcnow()
        return [
            {
                "opportunity_id": o.opportunity_id,
                "stage": o.current_stage.stage_name if o.current_stage else None,
                "age_days": max(0, (now - DashboardRepository._last_stage_change(o)).days),
            }
            for o in opportunities
            if DashboardRepository._last_stage_change(o)
        ]

    @staticmethod
    def get_average_stage_ageing(user, active_role):
        ages = [row["age_days"] for row in DashboardRepository.get_stage_ageing(user, active_role)]
        return 0 if not ages else round(sum(ages) / len(ages), 1)

    @staticmethod
    def get_stalled_deals(user, active_role):
        limit_date = datetime.utcnow() - timedelta(days=14)
        opportunities = DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.status.in_(["Open", "Approved", "Active"]),
            Opportunity.is_active.is_(True),
        ).all()
        return sum(
            1 for opportunity in opportunities
            if DashboardRepository._last_stage_change(opportunity) < limit_date
        )

    @staticmethod
    def get_active_pocs(user, active_role):
        ids = DashboardRepository._opportunity_ids(user, active_role)
        return Opportunity.query.filter(
            Opportunity.opportunity_id.in_(ids),
            Opportunity.is_active.is_(True),
        ).join(StageMaster).filter(
            StageMaster.stage_name == "POC / Technical Evaluation"
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
        # Start from the authorized opportunity scope, then left-join it to
        # every stage in StageMaster so the dashboard always receives the
        # complete database-defined pipeline, including zero-count stages.
        visible = DashboardRepository._opportunities(user, active_role).with_entities(
            Opportunity.opportunity_id.label("opportunity_id"),
            Opportunity.stage_id.label("stage_id"),
            Opportunity.estimated_value.label("estimated_value"),
        ).subquery()

        rows = StageMaster.query.outerjoin(
            visible, visible.c.stage_id == StageMaster.stage_id
        ).with_entities(
            StageMaster.stage_name,
            func.count(visible.c.opportunity_id),
            func.coalesce(func.sum(visible.c.estimated_value), 0),
            StageMaster.display_order,
        ).group_by(
            StageMaster.stage_id, StageMaster.stage_name, StageMaster.display_order
        ).order_by(StageMaster.display_order.asc()).all()

        return [
            {"stage": row[0], "count": row[1], "value": float(row[2] or 0)}
            for row in rows
        ]

    @staticmethod
    def get_recent_opportunities(user, active_role, limit=5):
        opportunities = DashboardRepository._opportunities(user, active_role).filter(
            Opportunity.is_active.is_(True)
        ).order_by(Opportunity.updated_at.desc()).limit(limit).all()
        return [
            {
                "id": o.opportunity_id,
                "name": o.opportunity_name,
                "account": o.account.account_name if o.account else "-",
                "stage": o.current_stage.stage_name if o.current_stage else "-",
                "value": float(o.estimated_value or 0),
                "probability": o.probability or 0,
                "status": o.status,
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
            POCTracker.status.in_([POC_STATUS_APPROVED, POC_STATUS_IN_PROGRESS]),
        ).order_by(POCTracker.target_date.asc()).limit(limit).all()
        return [
            {
                "id": p.poc_id,
                "opportunity": p.opportunity.opportunity_name if p.opportunity else "-",
                "objective": p.objective,
                "target_date": p.target_date,
                "status": p.status,
                "stakeholder_signoff": "Signed" if p.stakeholder_signoff else "Pending sign-off",
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
