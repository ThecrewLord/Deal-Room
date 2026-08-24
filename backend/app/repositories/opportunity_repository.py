from app.database import db
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.auth.user import User
from app.constants.roles import PRE_SALES_MANAGER, SALES_EXECUTIVE, SOLUTION_ENGINEER
from app.constants.auth_constants import STATUS_APPROVED


class OpportunityRepository:

    @staticmethod
    def create(opportunity):
        try:
            db.session.add(opportunity)
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all(query=None):
        query = query if query is not None else Opportunity.query
        return query.order_by(Opportunity.created_at.desc()).all()

    @staticmethod
    def get_by_id(opportunity_id, query=None):
        query = query if query is not None else Opportunity.query
        return query.filter_by(opportunity_id=opportunity_id).first()

    @staticmethod
    def get_by_account(account_id, query=None):
        query = query if query is not None else Opportunity.query
        return query.filter_by(account_id=account_id).all()

    @staticmethod
    def update():
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(opportunity):
        try:
            db.session.delete(opportunity)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def exists(name, account_id):
        return (
            Opportunity.query.filter_by(
                opportunity_name=name,
                account_id=account_id,
            ).first()
            is not None
        )

    @staticmethod
    def update_stage(opportunity, stage_id):
        try:
            opportunity.stage_id = stage_id
            db.session.commit()
            return opportunity
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_pending_sales_manager_review(query):
        return query.filter(
            Opportunity.status == "Pending Sales Manager Review",
            Opportunity.is_active.is_(True),
        ).order_by(Opportunity.updated_at.asc()).all()

    @staticmethod
    def get_eligible_sales_owners():
        return User.query.filter(
            User.active.is_(True),
            User.status == STATUS_APPROVED,
            User.roles.any(role=SALES_EXECUTIVE),
        ).order_by(User.full_name.asc()).all()

    @staticmethod
    def get_pending_pre_sales_assignment():
        technical_member = db.session.query(OpportunityTeam.team_id).filter(
            OpportunityTeam.opportunity_id == Opportunity.opportunity_id,
            OpportunityTeam.role == SOLUTION_ENGINEER,
        ).exists()
        return Opportunity.query.filter(
            Opportunity.status == "Approved",
            Opportunity.sales_owner_id.isnot(None),
            Opportunity.is_active.is_(True),
            ~technical_member,
        ).order_by(Opportunity.updated_at.asc()).all()

    @staticmethod
    def get_eligible_users(role):
        return User.query.filter(
            User.active.is_(True),
            User.status == STATUS_APPROVED,
            User.roles.any(role=role),
        ).order_by(User.full_name.asc()).all()
