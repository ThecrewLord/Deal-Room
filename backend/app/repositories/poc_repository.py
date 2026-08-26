from app.database import db
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.constants.roles import SOLUTION_ENGINEER
from sqlalchemy import and_


class PocRepository:
    @staticmethod
    
    def create(data):
        poc = POCTracker(**data)
        db.session.add(poc)
        db.session.flush()
        return poc

    @staticmethod
    def get_by_id(poc_id):
        return POCTracker.query.get(poc_id)

    @staticmethod
    def get_opportunity(opportunity_id):
        return Opportunity.query.get(opportunity_id)

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return POCTracker.query.filter_by(opportunity_id=opportunity_id).order_by(POCTracker.created_at.asc()).all()

    @staticmethod
    def get_pending_approval():
        return POCTracker.query.filter_by(status="Pending Approval").order_by(POCTracker.created_at.asc()).all()

    @staticmethod
    def get_for_solution_engineer(user_id):
        return (
            POCTracker.query.join(
                OpportunityTeam,
                OpportunityTeam.opportunity_id == POCTracker.opportunity_id,
            )
            .filter(
                OpportunityTeam.user_id == user_id,
                OpportunityTeam.role == SOLUTION_ENGINEER,
                POCTracker.status.in_(["Approved", "In Progress"]),
            )
            .order_by(POCTracker.created_at.asc())
            .all()
        )

    get_for_delivery = get_for_solution_engineer

    @staticmethod
    def update(poc, data):
        for key, value in data.items():
            setattr(poc, key, value)
        return poc

    @staticmethod
    def delete(poc):
        return False
