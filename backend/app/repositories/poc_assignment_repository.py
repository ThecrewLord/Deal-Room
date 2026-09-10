from app.database import db
from app.models.poc.poc_assignment import POCAssignment


class PocAssignmentRepository:

    @staticmethod
    def create(data):
        assignment = POCAssignment(**data)
        db.session.add(assignment)
        db.session.flush()
        return assignment

    @staticmethod
    def get_by_id(assignment_id):
        return db.session.get(POCAssignment, assignment_id)

    @staticmethod
    def get_active_by_poc(poc_id):
        return (
            POCAssignment.query
            .filter_by(
                poc_id=poc_id,
                is_active=True,
            )
            .order_by(POCAssignment.assigned_at.asc())
            .all()
        )

    @staticmethod
    def get_by_poc_and_user(poc_id, user_id):
        return (
            POCAssignment.query
            .filter_by(
                poc_id=poc_id,
                user_id=user_id,
            )
            .first()
        )

    @staticmethod
    def deactivate(assignment):
        assignment.is_active = False
        return assignment
