from app.database import db
from app.models.opportunity.stakeholder import Stakeholder


class StakeholderRepository:

    @staticmethod
    def create(data):
        stakeholder = Stakeholder(**data)
        db.session.add(stakeholder)
        db.session.commit()
        return stakeholder

    @staticmethod
    def get_by_id(stakeholder_id):
        return Stakeholder.query.get(stakeholder_id)

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return Stakeholder.query.filter_by(
            opportunity_id=opportunity_id
        ).all()

    @staticmethod
    def update(stakeholder, data):
        for key, value in data.items():
            setattr(stakeholder, key, value)
        db.session.commit()
        return stakeholder

    @staticmethod
    def delete(stakeholder):
        db.session.delete(stakeholder)
        db.session.commit()
        return True
