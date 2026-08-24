from datetime import datetime, timedelta

from app.constants.roles import SALES_EXECUTIVE, SALES_MANAGER
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster


class SalesManagerPerformanceService:
    """Performance reporting for a Sales Manager's direct Sales Executive reports."""

    STALLED_DAYS = 14

    @staticmethod
    def _direct_reports(manager):
        return (
            User.query
            .filter(
                User.manager_id == manager.user_id,
                User.active.is_(True),
                User.status == "APPROVED",
            )
            .order_by(User.full_name.asc())
            .all()
        )

    @staticmethod
    def _owned_opportunities(employee):
        return Opportunity.query.filter(
            Opportunity.sales_owner_id == employee.user_id
        )

    @staticmethod
    def _last_stage_change(opportunity):
        if opportunity.stage_history:
            return opportunity.stage_history[-1].created_at
        return opportunity.updated_at or opportunity.created_at

    @classmethod
    def _metrics(cls, employee):
        opportunities = cls._owned_opportunities(employee).all()
        open_opportunities = [
            o for o in opportunities
            if o.is_active and o.status in {"Open", "Approved", "Active"}
        ]
        closed_won = [
            o for o in opportunities
            if o.current_stage and o.current_stage.is_won
        ]
        closed_lost = [
            o for o in opportunities
            if o.current_stage and o.current_stage.is_closed and not o.current_stage.is_won
        ]

        pipeline_value = sum(float(o.estimated_value or 0) for o in open_opportunities)
        weighted_forecast = sum(
            float(o.estimated_value or 0) * float(o.probability or 0) / 100
            for o in open_opportunities
        )

        now = datetime.utcnow()
        active_ages = [
            max(0, (now - cls._last_stage_change(o)).days)
            for o in open_opportunities
            if cls._last_stage_change(o)
        ]
        stalled = sum(age > cls.STALLED_DAYS for age in active_ages)
        closed_total = len(closed_won) + len(closed_lost)

        return {
            "pipeline_value": round(pipeline_value, 2),
            "weighted_forecast": round(weighted_forecast, 2),
            "open_opportunities": len(open_opportunities),
            "total_opportunities": len(opportunities),
            "closed_won": len(closed_won),
            "closed_lost": len(closed_lost),
            "win_rate": round((len(closed_won) / closed_total) * 100, 1) if closed_total else 0,
            "stalled_deals": stalled,
            "average_stage_age_days": round(sum(active_ages) / len(active_ages), 1) if active_ages else 0,
            "average_deal_value": round(
                sum(float(o.estimated_value or 0) for o in open_opportunities) / len(open_opportunities),
                2,
            ) if open_opportunities else 0,
            "unassigned_submissions": sum(
                1 for o in opportunities
                if o.status == "Pending Sales Manager Review" and o.sales_owner_id is None
            ),
        }

    @classmethod
    def _employee_summary(cls, employee):
        return {
            "user_id": employee.user_id,
            "full_name": employee.full_name,
            "email": employee.email,
            "metrics": cls._metrics(employee),
        }

    @classmethod
    def team_performance(cls, manager):
        employees = cls._direct_reports(manager)
        rows = [cls._employee_summary(employee) for employee in employees]

        return {
            "manager": {
                "user_id": manager.user_id,
                "full_name": manager.full_name,
                "email": manager.email,
            },
            "team_size": len(rows),
            "employees": rows,
        }

    @classmethod
    def employee_performance(cls, manager, employee_id):
        employee = User.query.filter(
            User.user_id == employee_id,
            User.manager_id == manager.user_id,
            User.active.is_(True),
            User.status == "APPROVED",
            ).first()

        if not employee or not employee.has_role(SALES_EXECUTIVE):
            return None

        opportunities = (
            cls._owned_opportunities(employee)
            .order_by(Opportunity.updated_at.desc())
            .all()
        )
        metrics = cls._metrics(employee)

        stages = StageMaster.query.order_by(StageMaster.display_order.asc()).all()
        pipeline_by_stage = []
        for stage in stages:
            stage_opportunities = [
                o for o in opportunities
                if o.stage_id == stage.stage_id
            ]
            pipeline_by_stage.append({
                "stage": stage.stage_name,
                "count": len(stage_opportunities),
                "value": round(
                    sum(float(o.estimated_value or 0) for o in stage_opportunities), 2
                ),
            })

        return {
            "employee": {
                "user_id": employee.user_id,
                "full_name": employee.full_name,
                "email": employee.email,
                "role": SALES_EXECUTIVE,
            },
            "metrics": metrics,
            "pipeline_by_stage": pipeline_by_stage,
            "recent_opportunities": [
                {
                    "id": o.opportunity_id,
                    "name": o.opportunity_name,
                    "stage": o.current_stage.stage_name if o.current_stage else None,
                    "status": o.status,
                    "value": float(o.estimated_value or 0),
                    "probability": o.probability or 0,
                    "expected_close_date": (
                        o.expected_close_date.isoformat()
                        if o.expected_close_date else None
                    ),
                }
                for o in opportunities[:10]
            ],
        }
