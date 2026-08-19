from flask import Blueprint
from app.controllers.account_controller import AccountController

account_bp = Blueprint("account", __name__, url_prefix="/api/accounts")

account_bp.route("", methods=["POST"])(AccountController.create)
account_bp.route("", methods=["GET"])(AccountController.get_all)
account_bp.route("/<int:account_id>", methods=["GET"])(AccountController.get)
account_bp.route("/<int:account_id>", methods=["PUT"])(AccountController.update)
account_bp.route("/<int:account_id>", methods=["DELETE"])(AccountController.delete)
