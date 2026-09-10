from app.auth.authorization import AuthorizationService, AuthorizationDenied
from app.constants.roles import SALES_EXECUTIVE
from app.database import db
from app.models.account.account import Account
from app.repositories.account_repository import AccountRepository


class AccountService:

    @staticmethod
    def get_all(user, active_role):
        return AccountRepository.get_all(
            AuthorizationService.account_query(user, active_role)
        )

    @staticmethod
    def get_by_id(account_id, user, active_role):
        return AccountRepository.get_by_id(
            account_id,
            AuthorizationService.account_query(user, active_role),
        )

    @staticmethod
    def search(search_term, user, active_role):
        if not search_term or not search_term.strip():
            return AccountService.get_all(user, active_role)

        query = AuthorizationService.account_query(
            user,
            active_role,
        )

        return AccountRepository.search(
            search_term.strip(),
            query,
        )

    @staticmethod
    def create(data, user, active_role):
        if active_role != SALES_EXECUTIVE:
            raise AuthorizationDenied(
                "Only a Sales Executive can create an account."
            )

        normalized_name = data["account_name"].strip()

        if len(normalized_name) < 2:
            raise ValueError(
                "Account name must contain at least 2 characters."
            )

        existing = Account.query.filter_by(
            account_name=normalized_name
        ).first()

        if existing:
            if not AuthorizationService.can_view_account(
                user,
                active_role,
                existing,
            ):
                raise AuthorizationDenied(
                    "You are not authorized to use this account."
                )

            return existing

        account = Account(
            account_name=normalized_name,
            industry=data.get("industry"),
            website=data.get("website"),
            phone=data.get("phone"),
            country=data.get("country"),
            state=data.get("state"),
            city=data.get("city"),
            address=data.get("address"),
            is_active=True,
        )

        db.session.add(account)
        db.session.commit()

        return account

    @staticmethod
    def update(account_id, data, user, active_role):
        if active_role != SALES_EXECUTIVE:
            raise AuthorizationDenied(
                "Only a Sales Executive can update an account."
            )

        account = AccountRepository.get_by_id(
            account_id,
            AuthorizationService.account_query(user, active_role),
        )

        if not account:
            return None

        if "account_name" in data:
            normalized_name = data["account_name"].strip()

            if len(normalized_name) < 2:
                raise ValueError(
                    "Account name must contain at least 2 characters."
                )

            duplicate = Account.query.filter(
                Account.account_name == normalized_name,
                Account.account_id != account_id,
            ).first()

            if duplicate:
                raise ValueError(
                    "An account with this name already exists."
                )

            account.account_name = normalized_name

        if "industry" in data:
            account.industry = data["industry"]

        if "website" in data:
            account.website = data["website"]

        if "phone" in data:
            account.phone = data["phone"]

        if "country" in data:
            account.country = data["country"]

        if "state" in data:
            account.state = data["state"]

        if "city" in data:
            account.city = data["city"]

        if "address" in data:
            account.address = data["address"]

        db.session.commit()

        return account

    @staticmethod
    def archive(account_id, user, active_role):
        if active_role != SALES_EXECUTIVE:
            raise AuthorizationDenied(
                "Only a Sales Executive can archive an account."
            )

        account = AccountRepository.get_by_id(
            account_id,
            AuthorizationService.account_query(user, active_role),
        )

        if not account:
            return None

        account.is_active = False

        db.session.commit()

        return account