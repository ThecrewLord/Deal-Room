from app.database import db
from app.models.delivery.delivery_project import DeliveryProject


class DeliveryProjectRepository:

    @staticmethod
    def create(data):
        project = DeliveryProject(**data)
        db.session.add(project)
        db.session.flush()
        return project

    @staticmethod
    def get_by_id(project_id):
        return db.session.get(
            DeliveryProject,
            project_id,
        )

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return (
            DeliveryProject.query
            .filter_by(
                opportunity_id=opportunity_id
            )
            .order_by(
                DeliveryProject.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_by_poc(poc_id):
        return (
            DeliveryProject.query
            .filter_by(
                poc_id=poc_id
            )
            .order_by(
                DeliveryProject.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_pending():
        return (
            DeliveryProject.query
            .filter_by(
                status="Pending Assignment"
            )
            .order_by(
                DeliveryProject.created_at.asc()
            )
            .all()
        )

    @staticmethod
    def update(project, data):
        for key, value in data.items():
            setattr(project, key, value)

        db.session.flush()
        return project

    @staticmethod
    def delete(project):
        db.session.delete(project)
        db.session.flush()

    @staticmethod
    def get_pending_poc_assignments():
        """
        Return completed POCs that do not yet have a delivery project.
        """
        from app.models.opportunity.poc_tracker import POCTracker

        completed_pocs = (
            POCTracker.query
            .filter_by(status="Completed")
            .order_by(POCTracker.target_date.asc())
            .all()
        )

        return [
            poc
            for poc in completed_pocs
            if not DeliveryProjectRepository.get_by_poc(poc.poc_id)
        ]

