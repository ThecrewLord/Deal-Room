from app.database import db
from app.models.account.account import Account
from app.models.account.oem_partner import OEMPartner


class OEMRepository:
    @staticmethod
    def get_all():
        return OEMPartner.query.all()

    @staticmethod
    def get_by_accounts(account_query):
        account_ids = account_query.with_entities(Account.account_id).subquery()
        return OEMPartner.query.filter(OEMPartner.account_id.in_(account_ids)).all()

    @staticmethod
    def get_by_id(oem_id):
        return OEMPartner.query.get(oem_id)

    @staticmethod
    def get_account(account_id):
        return Account.query.get(account_id)

    @staticmethod
    def create_from_data(data):
        oem = OEMPartner(**data)
        db.session.add(oem)
        db.session.commit()
        return oem

    @staticmethod
    def get_by_partner_name(partner_name):
        return OEMPartner.query.filter_by(partner_name=partner_name).first()
