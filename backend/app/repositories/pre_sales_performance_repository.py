from datetime import datetime, timedelta

from sqlalchemy import func

from app.constants.auth_constants import STATUS_APPROVED
from app.constants.poc_outcome import (
    POC_STATUS_APPROVED,
    POC_STATUS_COMPLETED,
    POC_STATUS_IN_PROGRESS,
    POC_STATUS_PENDING_APPROVAL,
    POC_STATUS_REJECTED,
    POC_STATUS_SUBMITTED,
)
from app.constants.roles import SOLUTION_ENGINEER
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stage_master import StageMaster


class PreSalesPerformanceRepository:
    """Read-only technical performance queries for a Pre-Sales Manager's reports."""

    @staticmethod
    def get_direct_reports(manager_id):
        return User.query.filter(
            User.manager_id == manager_id,
            User.active.is_(True),
            User.status == STATUS_APPROVED,
            User.roles.any(UserRole.role == SOLUTION_ENGINEER),
        ).order_by(User.full_name.asc()).all()

    @staticmethod
    def _team_rows(employee_id):
        return OpportunityTeam.query.filter(
            OpportunityTeam.user_id == employee_id,
            OpportunityTeam.role == SOLUTION_ENGINEER,
        )

    @staticmethod
    def _opportunity_ids(employee_id):
        return [row[0] for row in PreSalesPerformanceRepository._team_rows(employee_id).with_entities(OpportunityTeam.opportunity_id).distinct().all()]

    @staticmethod
    def _opportunities(employee_id):
        ids = PreSalesPerformanceRepository._opportunity_ids(employee_id)
        if not ids:
            return Opportunity.query.filter(Opportunity.opportunity_id == -1)
        return Opportunity.query.filter(Opportunity.opportunity_id.in_(ids))

    @staticmethod
    def _last_stage_change(opportunity):
        if opportunity.stage_history:
            return opportunity.stage_history[-1].created_at
        return opportunity.updated_at or opportunity.created_at

    @staticmethod
    def get_metrics(employee_id):
        opportunities = PreSalesPerformanceRepository._opportunities(employee_id)
        total = opportunities.count()
        active = opportunities.filter(
            Opportunity.is_active.is_(True),
            Opportunity.status.in_(["Approved", "Active", "Open"]),
        ).all()
        assigned_value = sum(float(o.estimated_value or 0) for o in active)
        weighted_forecast = sum(
            float(o.estimated_value or 0) * float(o.probability or 0) / 100 for o in active
        )

        pocs = POCTracker.query.filter(POCTracker.opportunity_id.in_(
            [o.opportunity_id for o in opportunities.all()]
        )).all() if total else []
        active_pocs = sum(p.status in {POC_STATUS_APPROVED, POC_STATUS_IN_PROGRESS, POC_STATUS_SUBMITTED} for p in pocs)
        completed_pocs = sum(p.status == POC_STATUS_COMPLETED for p in pocs)
        pending_pocs = sum(p.status == POC_STATUS_PENDING_APPROVAL for p in pocs)
        rejected_pocs = sum(p.status == POC_STATUS_REJECTED for p in pocs)

        stalled = 0
        ages = []
        cutoff = datetime.utcnow() - timedelta(days=14)
        for opportunity in active:
            changed = PreSalesPerformanceRepository._last_stage_change(opportunity)
            if changed:
                age = max(0, (datetime.utcnow() - changed).days)
                ages.append(age)
                if changed < cutoff:
                    stalled += 1

        return {
            "assigned_opportunities": total,
            "active_opportunities": len(active),
            "assigned_value": round(assigned_value, 2),
            "weighted_forecast": round(weighted_forecast, 2),
            "active_pocs": active_pocs,
            "completed_pocs": completed_pocs,
            "pending_pocs": pending_pocs,
            "rejected_pocs": rejected_pocs,
            "stalled_opportunities": stalled,
            "average_stage_age_days": round(sum(ages) / len(ages), 1) if ages else 0,
        }

    @staticmethod
    def get_pipeline_by_stage(employee_id):
        ids = PreSalesPerformanceRepository._opportunity_ids(employee_id)
        if not ids:
            return []
        rows = StageMaster.query.outerjoin(
            Opportunity,
            (Opportunity.stage_id == StageMaster.stage_id)
            & Opportunity.opportunity_id.in_(ids),
        ).with_entities(
            StageMaster.stage_name,
            func.count(Opportunity.opportunity_id),
            func.coalesce(func.sum(Opportunity.estimated_value), 0),
            StageMaster.display_order,
        ).group_by(
            StageMaster.stage_id,
            StageMaster.stage_name,
            StageMaster.display_order,
        ).order_by(StageMaster.display_order.asc()).all()
        return [{"stage": row[0], "count": row[1], "value": float(row[2] or 0)} for row in rows]

    @staticmethod
    def get_poc_by_status(employee_id):
        ids = PreSalesPerformanceRepository._opportunity_ids(employee_id)
        if not ids:
            return []
        rows = POCTracker.query.filter(POCTracker.opportunity_id.in_(ids)).with_entities(
            POCTracker.status, func.count(POCTracker.poc_id)
        ).group_by(POCTracker.status).all()
        return [{"status": row[0], "count": row[1]} for row in rows]

    @staticmethod
    def get_recent_work(employee_id, limit=10):
        ids = PreSalesPerformanceRepository._opportunity_ids(employee_id)
        if not ids:
            return []
        opportunities = Opportunity.query.filter(
            Opportunity.opportunity_id.in_(ids)
        ).order_by(Opportunity.updated_at.desc()).limit(limit).all()
        return [
            {
                "id": o.opportunity_id,
                "name": o.opportunity_name,
                "stage": o.current_stage.stage_name if o.current_stage else "-",
                "status": o.status,
                "value": float(o.estimated_value or 0),
                "probability": o.probability or 0,
                "expected_close_date": o.expected_close_date,
                "updated_at": o.updated_at,
            }
            for o in opportunities
        ]
