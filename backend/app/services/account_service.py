from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, text
from app.auth.authorization import AuthorizationService, AuthorizationDenied
from app.database import db
from app.models.account.account import Account
from app.services.activity_service import ActivityService

def canonicalize(name):
    return " ".join(str(name or "").strip().lower().split())

class AccountService:
    @staticmethod
    def get_all(user, active_role):
        return AuthorizationService.account_query(user, active_role).order_by(Account.account_name.asc()).all()

    @staticmethod
    def get_by_id(account_id, user, active_role):
        return AuthorizationService.account_query(user, active_role).filter(Account.account_id == account_id).first()

    @staticmethod
    def create(data, user, active_role):
        if not AuthorizationService.can_create_account(user, active_role):
            raise AuthorizationDenied("You are not authorized to create accounts.")
        name = str(data.get("account_name") or "").strip()
        if len(name) < 2:
            raise ValueError("Account name must contain at least 2 characters.")
        canonical = canonicalize(name)
        if Account.query.filter_by(canonical_name=canonical).first():
            raise ValueError("An account with this canonical identity already exists.")
        account = Account(account_name=name, canonical_name=canonical, status="Active", is_active=True,
                          industry=data.get("industry"), website=data.get("website"), phone=data.get("phone"),
                          country=data.get("country"), state=data.get("state"), city=data.get("city"), address=data.get("address"))
        try:
            db.session.add(account); db.session.flush()
            ActivityService.log("Account", account.account_id, "ACCOUNT_CREATED",
                                f"Account '{account.account_name}' created.", user.user_id, commit=False, active_role=active_role)
            db.session.commit()
            return account
        except IntegrityError:
            db.session.rollback()
            raise ValueError("An account with this canonical identity already exists.")

    @staticmethod
    def archive(account_id, user, active_role):
        account = Account.query.get(account_id)
        if not AuthorizationService.can_govern_account(user, active_role, account):
            raise AuthorizationDenied("Only Leadership can archive accounts.")
        if account.status == "Archived":
            raise ValueError("Account is already archived.")
        account.status, account.is_active = "Archived", False
        ActivityService.log("Account", account.account_id, "ACCOUNT_ARCHIVED", f"Account '{account.account_name}' archived.", user.user_id, commit=False, active_role=active_role)
        db.session.commit(); return account

    @staticmethod
    def ban(account_id, user, active_role):
        account = Account.query.get(account_id)
        if not AuthorizationService.can_govern_account(user, active_role, account):
            raise AuthorizationDenied("Only Leadership can ban accounts.")
        if account.status == "Banned":
            raise ValueError("Account is already banned.")
        account.status, account.is_active = "Banned", False
        ActivityService.log("Account", account.account_id, "ACCOUNT_BANNED", f"Account '{account.account_name}' banned.", user.user_id, commit=False, active_role=active_role)
        db.session.commit(); return account

    @staticmethod
    def delete_duplicate(account_id, user, active_role):
        account = Account.query.get(account_id)
        if not AuthorizationService.can_govern_account(user, active_role, account):
            raise AuthorizationDenied("Only Leadership can perform duplicate cleanup.")
        if account.opportunities:
            raise ValueError("Historical opportunities prevent physical deletion.")
        db.session.delete(account)
        ActivityService.log("Account", account_id, "ACCOUNT_DUPLICATE_DELETED", "Duplicate-resolution account deleted.", user.user_id, commit=False, active_role=active_role)
        db.session.commit()
