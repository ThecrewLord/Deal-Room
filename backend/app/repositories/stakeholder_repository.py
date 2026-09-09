from app.database import db
from sqlalchemy import func
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.stakeholder import Stakeholder


class StakeholderRepository:
    @staticmethod
    def create(data):
        # Seed/import workflows can insert explicit stakeholder IDs and leave
        # PostgreSQL's serial sequence behind. Letting the database generate
        # the next ID can then produce a duplicate-primary-key 409. Compute
        # the next ID from the current table contents so local development and
        # seeded databases remain writable.
        payload = dict(data)
        if not payload.get("stakeholder_id"):
            max_id = db.session.query(func.max(Stakeholder.stakeholder_id)).scalar() or 0
            payload["stakeholder_id"] = int(max_id) + 1
        stakeholder = Stakeholder(**payload)
        db.session.add(stakeholder)
        return stakeholder

    @staticmethod
    def get_by_id(stakeholder_id):
        return Stakeholder.query.get(stakeholder_id)

    @staticmethod
    def get_opportunity(opportunity_id):
        return Opportunity.query.get(opportunity_id)

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return Stakeholder.query.filter_by(opportunity_id=opportunity_id).all()

    @staticmethod
    def update(stakeholder, data):
        for key, value in data.items():
            setattr(stakeholder, key, value)
        return stakeholder

    @staticmethod
    def delete(stakeholder):
        db.session.delete(stakeholder)
        db.session.commit()
        return True
