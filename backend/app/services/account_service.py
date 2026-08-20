from app.repositories.account_repository import AccountRepository


class AccountService:

    @staticmethod
    def create_account(data):
        existing = AccountRepository.get_by_name(data["account_name"])
        if existing:
            raise ValueError(
                f"An account named '{data['account_name']}' already exists."
            )
        return AccountRepository.create(data)

    @staticmethod
    def get_all():
        return AccountRepository.get_all()

    @staticmethod
    def get_by_id(account_id):
        return AccountRepository.get_by_id(account_id)

    @staticmethod
    def update_account(account_id, data):
        account = AccountRepository.get_by_id(account_id)

        if not account:
            return None

        incoming_updated_at = data.pop("updated_at", None)

        if incoming_updated_at and account.updated_at:
            if incoming_updated_at.replace(tzinfo=None) != account.updated_at.replace(tzinfo=None):
                raise RuntimeError(
                    "This account was updated by someone else. Please reload and try again."
                )

        return AccountRepository.update(account, data)

    @staticmethod
    def delete_account(account_id):
        account = AccountRepository.get_by_id(account_id)

        if not account:
            return False

        return AccountRepository.delete(account)
