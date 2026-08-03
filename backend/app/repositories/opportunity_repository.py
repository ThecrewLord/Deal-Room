from app.database import db
from app.models.opportunity.opportunity import Opportunity


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
    def get_all():
        return (
            Opportunity.query
            .order_by(Opportunity.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(opportunity_id):
        return Opportunity.query.filter_by(
            opportunity_id=opportunity_id
        ).first()

    @staticmethod
    def get_by_account(account_id):
        return Opportunity.query.filter_by(
            account_id=account_id
        ).all()

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
            )
            .first()
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