from app.database import db
from app.models.delivery.delivery_assignment import DeliveryAssignment


class DeliveryAssignmentRepository:

    @staticmethod
    def create(data):
        assignment = DeliveryAssignment(**data)

        db.session.add(assignment)
        db.session.flush()

        return assignment

    @staticmethod
    def get_by_id(assignment_id):
        return db.session.get(
            DeliveryAssignment,
            assignment_id,
        )

    @staticmethod
    def get_active_by_project(project_id):
        return (
            DeliveryAssignment.query
            .filter_by(
                project_id=project_id,
                is_active=True,
            )
            .order_by(
                DeliveryAssignment.assigned_at.asc()
            )
            .all()
        )

    @staticmethod
    def get_by_project_and_user(
        project_id,
        user_id,
    ):
        return (
            DeliveryAssignment.query
            .filter_by(
                project_id=project_id,
                user_id=user_id,
            )
            .first()
        )

    @staticmethod
    def deactivate(assignment):
        assignment.is_active = False

        db.session.flush()

        return assignment