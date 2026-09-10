from app.models.account.account import Account


class AccountRepository:

    @staticmethod
    def get_all(query):
        return query.order_by("account_name").all()

    @staticmethod
    def get_by_id(account_id, query):
        return query.filter_by(account_id=account_id).first()

    @staticmethod
    def search(search_term, query):
        return query.filter(
            Account.account_name.ilike(f"%{search_term}%")
        ).order_by(
            Account.account_name
        ).all()