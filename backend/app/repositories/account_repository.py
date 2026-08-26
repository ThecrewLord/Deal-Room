class AccountRepository:
    @staticmethod
    def get_all(query):
        return query.order_by("account_name").all()

    @staticmethod
    def get_by_id(account_id, query):
        return query.filter_by(account_id=account_id).first()
