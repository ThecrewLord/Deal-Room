from datetime import date

from app.auth.authorization import AuthorizationService
from app.database import db
from app.models.auth.user import User
from app.models.delivery.delivery_project import DeliveryProject
from app.models.delivery.delivery_assignment import DeliveryAssignment


class DeliveryDashboardService:

    @staticmethod
    def _authorize(user, active_role):
        if not AuthorizationService.can_view_pending_delivery_assignments(
            user, active_role
        ):
            raise ValueError(
                "Only a Delivery Manager can view the delivery dashboard."
            )

    @staticmethod
    def get_dashboard(user, active_role):
        DeliveryDashboardService._authorize(user, active_role)

        projects = (
            DeliveryProject.query
            .order_by(DeliveryProject.created_at.desc())
            .all()
        )

        pending_assignments = [
            p for p in projects
            if p.status == "Pending Assignment"
        ]

        active_projects = [
            p for p in projects
            if p.status in {"Assigned", "In Progress"}
        ]

        in_progress = [
            p for p in projects
            if p.status == "In Progress"
        ]

        done = [
            p for p in projects
            if p.status == "Done"
        ]

        today = date.today()

        overdue = [
            p for p in projects
            if p.target_date
            and p.target_date < today
            and p.status != "Done"
        ]

        upcoming = [
            p for p in projects
            if p.target_date
            and p.target_date >= today
            and p.status != "Done"
        ]

        assignments = (
            DeliveryAssignment.query
            .filter_by(is_active=True)
            .all()
        )

        team_workload = {}

        for assignment in assignments:
            user_record = db.session.get(User, assignment.user_id)

            if not user_record:
                continue

            user_id = assignment.user_id

            if user_id not in team_workload:
                team_workload[user_id] = {
                    "user_id": user_id,
                    "user_name": user_record.full_name,
                    "role": assignment.role,
                    "active_projects": 0,
                }

            team_workload[user_id]["active_projects"] += 1

        return {
            "summary": {
                "total_projects": len(projects),
                "pending_assignments": len(pending_assignments),
                "active_projects": len(active_projects),
                "in_progress": len(in_progress),
                "done": len(done),
                "overdue": len(overdue),
                "upcoming": len(upcoming),
            },
            "pending_assignments": [
                DeliveryDashboardService._serialize_project(p)
                for p in pending_assignments
            ],
            "active_projects": [
                DeliveryDashboardService._serialize_project(p)
                for p in active_projects
            ],
            "in_progress": [
                DeliveryDashboardService._serialize_project(p)
                for p in in_progress
            ],
            "overdue": [
                DeliveryDashboardService._serialize_project(p)
                for p in overdue
            ],
            "upcoming": [
                DeliveryDashboardService._serialize_project(p)
                for p in upcoming
            ],
            "done": [
                DeliveryDashboardService._serialize_project(p)
                for p in done
            ],
            "team_workload": list(team_workload.values()),
        }

    @staticmethod
    def _serialize_project(project):
        assignments = [
            {
                "assignment_id": assignment.assignment_id,
                "user_id": assignment.user_id,
                "role": assignment.role,
                "assigned_at": (
                    assignment.assigned_at.isoformat()
                    if assignment.assigned_at
                    else None
                ),
            }
            for assignment in project.assignments
            if assignment.is_active
        ]

        return {
            "project_id": project.project_id,
            "opportunity_id": project.opportunity_id,
            "poc_id": project.poc_id,
            "project_name": project.project_name,
            "status": project.status,
            "start_date": (
                project.start_date.isoformat()
                if project.start_date
                else None
            ),
            "target_date": (
                project.target_date.isoformat()
                if project.target_date
                else None
            ),
            "created_by": project.created_by,
            "assignments": assignments,
        }
