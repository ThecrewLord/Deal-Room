from flask import g, jsonify, request
from marshmallow import ValidationError

from app.auth.authorization import AuthorizationDenied
from app.schemas.account_schema import AccountCreateSchema
from app.services.account_service import AccountService


create_schema = AccountCreateSchema()


class AccountController:
    @staticmethod
    def get_all(user, active_role):
        accounts = AccountService.get_all(user, active_role)
        return jsonify([
            {
                "account_id": account.account_id,
                "account_name": account.account_name,
                "industry": account.industry,
                "website": account.website,
                "phone": account.phone,
                "country": account.country,
                "state": account.state,
                "city": account.city,
                "address": account.address,
                "is_active": account.is_active,
            }
            for account in accounts
        ])

    @staticmethod
    def get(account_id, user, active_role):
        account = AccountService.get_by_id(account_id, user, active_role)
        if not account:
            return jsonify({"message": "Account not found"}), 404
        return jsonify({
            "account_id": account.account_id,
            "account_name": account.account_name,
            "industry": account.industry,
            "website": account.website,
            "phone": account.phone,
            "country": account.country,
            "state": account.state,
            "city": account.city,
            "address": account.address,
            "is_active": account.is_active,
        })

    @staticmethod
    def create(user, active_role):
        try:
            data = create_schema.load(request.get_json() or {})
            account = AccountService.create(data["account_name"], user, active_role)
            return jsonify({
                "account_id": account.account_id,
                "account_name": account.account_name,
                "industry": account.industry,
                "website": account.website,
                "phone": account.phone,
                "country": account.country,
                "state": account.state,
                "city": account.city,
                "address": account.address,
                "is_active": account.is_active,
            }), 201
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 409
