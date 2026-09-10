from flask import Blueprint, g

from app.auth.authorization import business_access_required
from app.controllers.account_controller import AccountController

account_bp = Blueprint("account", __name__, url_prefix="/api/accounts")


@account_bp.get("")
@business_access_required
def get_accounts():
    return AccountController.get_all(g.auth_user, g.active_role)


@account_bp.post("")
@business_access_required
def create_account():
    return AccountController.create(g.auth_user, g.active_role)

@account_bp.get("/<int:account_id>")
@business_access_required
def get_account(account_id):
    return AccountController.get(account_id, g.auth_user, g.active_role)

@account_bp.post("/<int:account_id>/archive")
@business_access_required
def archive_account(account_id):
    return AccountController.archive(account_id, g.auth_user, g.active_role)

@account_bp.post("/<int:account_id>/ban")
@business_access_required
def ban_account(account_id):
    return AccountController.ban(account_id, g.auth_user, g.active_role)

@account_bp.delete("/<int:account_id>/duplicate")
@business_access_required
def delete_duplicate_account(account_id):
    return AccountController.delete_duplicate(account_id, g.auth_user, g.active_role)
