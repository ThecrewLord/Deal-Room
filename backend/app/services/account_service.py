from app.auth.authorization import AuthorizationService, AuthorizationDenied
from app.constants.roles import SALES_EXECUTIVE
from app.database import db
from app.models.account.account import Account
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

    @staticmethod
    def create(account_name, user, active_role):
        if active_role != SALES_EXECUTIVE:
            raise AuthorizationDenied("Only a Sales Executive can create an account from an opportunity.")

        normalized_name = account_name.strip()
        if len(normalized_name) < 2:
            raise ValueError("Account name must contain at least 2 characters.")

        existing = Account.query.filter_by(account_name=normalized_name).first()
        if existing:
            if not AuthorizationService.can_view_account(user, active_role, existing):
                raise AuthorizationDenied("You are not authorized to use this account.")
            return existing

        account = Account(account_name=normalized_name, is_active=True)
        db.session.add(account)
        db.session.commit()
        return account
