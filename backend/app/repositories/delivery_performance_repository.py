from datetime import datetime, timedelta
from app.database import db
from app.constants.auth_constants import STATUS_APPROVED
from app.constants.roles import DEVOPS_ENGINEER, DATA_ANALYST
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.phase2 import DeliveryProject, DeliveryProjectMember


class DeliveryPerformanceRepository:
    """Read-only, manager-scoped delivery assignment aggregates."""

    @staticmethod
    def _eligible_role_filter():
        return User.roles.any(UserRole.role.in_([DEVOPS_ENGINEER, DATA_ANALYST]))

    @staticmethod
    def get_team_users(manager_id):
        direct_reports = User.query.filter(
            User.manager_id == manager_id,
            User.active.is_(True), User.status == STATUS_APPROVED,
            DeliveryPerformanceRepository._eligible_role_filter(),
        ).all()
        assigned_ids = [row[0] for row in db.session.query(DeliveryProjectMember.user_id)
            .join(DeliveryProject, DeliveryProject.delivery_project_id == DeliveryProjectMember.delivery_project_id)
            .filter(DeliveryProject.manager_id == manager_id).distinct().all()]
        assigned = User.query.filter(
            User.user_id.in_(assigned_ids) if assigned_ids else User.user_id == -1,
            User.active.is_(True), User.status == STATUS_APPROVED,
            DeliveryPerformanceRepository._eligible_role_filter(),
        ).all()
        by_id = {user.user_id: user for user in direct_reports + assigned}
        return sorted(by_id.values(), key=lambda user: ((user.full_name or "").lower(), user.user_id))

    @staticmethod
    def _member_query(employee_id):
        return DeliveryProjectMember.query.join(
            DeliveryProject, DeliveryProject.delivery_project_id == DeliveryProjectMember.delivery_project_id
        ).join(Opportunity, Opportunity.opportunity_id == DeliveryProject.opportunity_id).filter(
            DeliveryProjectMember.user_id == employee_id
        )

    @staticmethod
    def get_metrics(employee_id):
        rows = DeliveryPerformanceRepository._member_query(employee_id).all()
        assigned_opportunities = len({row.project.opportunity_id for row in rows})
        active_assignments = sum(1 for row in rows if row.project.status == "Active" and not row.is_done)
        completed_assignments = sum(1 for row in rows if row.is_done or row.project.status == "Done")
        now = datetime.utcnow()
        period_start = datetime(now.year, now.month, 1)
        completed_this_period = 0
        for row in rows:
            completed_at = row.completed_at or (row.project.completed_at if row.project.status == "Done" else None)
            if completed_at and completed_at >= period_start:
                completed_this_period += 1
        return {
            "assigned_opportunities": assigned_opportunities,
            "active_delivery_work": active_assignments,
            # No due-date field exists on DeliveryProject or DeliveryProjectMember.
            # None explicitly means not tracked; it must not be displayed as zero.
            "overdue_work": None,
            "completed_work": completed_this_period,
            "completed_assignments": completed_assignments,
            "reporting_period": "current_month",
            "overdue_tracking_available": False,
        }

    @staticmethod
    def get_pipeline_by_stage(employee_id):
        rows = DeliveryPerformanceRepository._member_query(employee_id).with_entities(
            Opportunity.opportunity_id, Opportunity.lifecycle_stage, Opportunity.estimated_value,
            Opportunity.outcome,
        ).distinct().all()
        stages = ["Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"]
        by_stage = {stage: {"stage": stage, "count": 0, "value": 0.0} for stage in stages}
        seen = set()
        for oid, stage, value, outcome in rows:
            if oid in seen:
                continue
            seen.add(oid)
            if stage in by_stage:
                by_stage[stage]["count"] += 1
                by_stage[stage]["value"] += float(value or 0)
        return [{**item, "value": round(item["value"], 2)} for item in by_stage.values()]

    @staticmethod
    def get_delivery_by_status(employee_id):
        rows = DeliveryPerformanceRepository._member_query(employee_id).all()
        counts = {"Active": 0, "Completed": 0}
        for member in rows:
            if member.is_done or member.project.status == "Done":
                counts["Completed"] += 1
            elif member.project.status == "Active":
                counts["Active"] += 1
        return [{"status": key, "count": value} for key, value in counts.items()]

    @staticmethod
    def get_recent_work(employee_id, limit=10):
        rows = DeliveryPerformanceRepository._member_query(employee_id).order_by(
            DeliveryProject.updated_at.desc(), DeliveryProject.delivery_project_id.desc()
        ).limit(limit).all()
        return [{
            "delivery_project_id": row.delivery_project_id,
            "opportunity_id": row.project.opportunity_id,
            "opportunity_name": row.project.opportunity.opportunity_name if row.project.opportunity else None,
            "stage": row.project.opportunity.lifecycle_stage if row.project.opportunity else None,
            "outcome": row.project.opportunity.outcome if row.project.opportunity else None,
            "project_status": row.project.status,
            "assignment_status": "Completed" if row.is_done or row.project.status == "Done" else "Active",
            "is_suggested": row.is_suggested,
            "value": float(row.project.opportunity.estimated_value or 0) if row.project.opportunity else 0,
            "expected_close_date": row.project.opportunity.expected_close_date.isoformat() if row.project.opportunity and row.project.opportunity.expected_close_date else None,
            "due_date": None,
            "completed_at": row.completed_at.isoformat() if row.completed_at else (row.project.completed_at.isoformat() if row.project.status == "Done" and row.project.completed_at else None),
            "updated_at": row.project.updated_at.isoformat() if row.project.updated_at else None,
        } for row in rows]


