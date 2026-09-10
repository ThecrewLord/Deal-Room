from app.database import db
from app.models.opportunity.opportunity_oem import OpportunityOEM


class OpportunityOEMRepository:

    @staticmethod
    def get_by_id(opportunity_oem_id):
        return OpportunityOEM.query.filter_by(
            opportunity_oem_id=opportunity_oem_id
        ).first()

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return (
            OpportunityOEM.query
            .filter_by(opportunity_id=opportunity_id)
            .order_by(OpportunityOEM.created_at.asc())
            .all()
        )

    @staticmethod
    def get_by_pair(opportunity_id, oem_partner_id):
        return OpportunityOEM.query.filter_by(
            opportunity_id=opportunity_id,
            oem_partner_id=oem_partner_id,
        ).first()

    @staticmethod
    def create(opportunity_oem):
        try:
            db.session.add(opportunity_oem)
            db.session.commit()
            return opportunity_oem
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(opportunity_oem):
        try:
            db.session.delete(opportunity_oem)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
