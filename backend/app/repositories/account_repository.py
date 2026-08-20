from app.database import db
from app.models.account.account import Account


class AccountRepository:

    @staticmethod
    def create(data):
        account = Account(**data)
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def get_all():
        return Account.query.order_by(Account.account_name).all()

    @staticmethod
    def get_by_id(account_id):
        return Account.query.get(account_id)

    @staticmethod
    def get_by_name(account_name):
        return Account.query.filter_by(account_name=account_name).first()

    @staticmethod
    def update(account, data):
        for key, value in data.items():
            setattr(account, key, value)
        db.session.commit()
        return account

    @staticmethod
    def delete(account):
        db.session.delete(account)
        db.session.commit()
        return True
