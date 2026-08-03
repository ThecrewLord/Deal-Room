from app.database import db
from app.models.account.oem_partner import OEMPartner


class OEMRepository:

    @staticmethod
    def get_all():
        return OEMPartner.query.all()

    @staticmethod
    def get_by_id(oem_id):
        return OEMPartner.query.get(oem_id)

    @staticmethod
    def create(oem):
        try:
            db.session.add(oem)
            db.session.commit()
            return oem
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update():
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete(oem):
        try:
            db.session.delete(oem)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_by_partner_name(partner_name):
        return OEMPartner.query.filter_by(
            partner_name=partner_name
        ).first()