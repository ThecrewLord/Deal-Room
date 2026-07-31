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
        db.session.add(oem)
        db.session.commit()
        return oem

    @staticmethod
    def update():
        db.session.commit()

    @staticmethod
    def delete(oem):
        db.session.delete(oem)
        db.session.commit()