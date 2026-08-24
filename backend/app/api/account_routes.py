from flask import Blueprint, g

from app.auth.authorization import business_access_required
from app.controllers.account_controller import AccountController

account_bp = Blueprint("account", __name__, url_prefix="/api/accounts")


@account_bp.get("")
@business_access_required
def get_accounts():
    return AccountController.get_all(g.auth_user, g.active_role)


@account_bp.get("/<int:account_id>")
@business_access_required
def get_account(account_id):
    return AccountController.get(account_id, g.auth_user, g.active_role)
