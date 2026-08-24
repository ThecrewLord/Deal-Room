from app.auth.authorization import AuthorizationService
from app.repositories.account_repository import AccountRepository


class AccountService:
    @staticmethod
    def get_all(user, active_role):
        return AccountRepository.get_all(AuthorizationService.account_query(user, active_role))

    @staticmethod
    def get_by_id(account_id, user, active_role):
        return AccountRepository.get_by_id(
            account_id,
            AuthorizationService.account_query(user, active_role),
        )
