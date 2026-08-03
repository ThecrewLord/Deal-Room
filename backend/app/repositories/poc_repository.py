from app.database import db
from app.models.opportunity.poc_tracker import POCTracker


class PocRepository:

    @staticmethod
    def create(data):
        poc = POCTracker(**data)
        db.session.add(poc)
        db.session.commit()
        return poc

    @staticmethod
    def get_by_id(poc_id):
        return POCTracker.query.get(poc_id)

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return POCTracker.query.filter_by(
            opportunity_id=opportunity_id
        ).all()

    @staticmethod
    def update(poc, data):
        for key, value in data.items():
            setattr(poc, key, value)
        db.session.commit()
        return poc

    @staticmethod
    def delete(poc):
        db.session.delete(poc)
        db.session.commit()
        return True