from flask import jsonify, request
from marshmallow import ValidationError

from app.auth.authorization import AuthorizationDenied
from app.schemas.account_schema import (
    AccountCreateSchema,
    AccountUpdateSchema,
)
from app.services.account_service import AccountService


create_schema = AccountCreateSchema()
update_schema = AccountUpdateSchema()


class AccountController:

    @staticmethod
    def _serialize(account):
        return {
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

    @staticmethod
    def get_all(user, active_role):
        accounts = AccountService.get_all(
            user,
            active_role,
        )

        return jsonify([
            AccountController._serialize(account)
            for account in accounts
        ])

    @staticmethod
    def get(account_id, user, active_role):
        account = AccountService.get_by_id(
            account_id,
            user,
            active_role,
        )

        if not account:
            return jsonify({
                "message": "Account not found"
            }), 404

        return jsonify(
            AccountController._serialize(account)
        )

    @staticmethod
    def search(user, active_role):
        search_term = request.args.get("q", "")

        accounts = AccountService.search(
            search_term,
            user,
            active_role,
        )

        return jsonify([
            AccountController._serialize(account)
            for account in accounts
        ])

    @staticmethod
    def create(user, active_role):
        try:
            data = create_schema.load(
                request.get_json() or {}
            )

            account = AccountService.create(
                data,
                user,
                active_role,
            )

            return jsonify(
                AccountController._serialize(account)
            ), 201

        except ValidationError as err:
            return jsonify(err.messages), 400

        except AuthorizationDenied as err:
            return jsonify({
                "message": str(err)
            }), 403

        except ValueError as err:
            return jsonify({
                "message": str(err)
            }), 409

    @staticmethod
    def update(account_id, user, active_role):
        try:
            data = update_schema.load(
                request.get_json() or {}
            )

            account = AccountService.update(
                account_id,
                data,
                user,
                active_role,
            )

            if not account:
                return jsonify({
                    "message": "Account not found"
                }), 404

            return jsonify(
                AccountController._serialize(account)
            )

        except ValidationError as err:
            return jsonify(err.messages), 400

        except AuthorizationDenied as err:
            return jsonify({
                "message": str(err)
            }), 403

        except ValueError as err:
            return jsonify({
                "message": str(err)
            }), 409

    @staticmethod
    def archive(account_id, user, active_role):
        try:
            account = AccountService.archive(
                account_id,
                user,
                active_role,
            )

            if not account:
                return jsonify({
                    "message": "Account not found"
                }), 404

            return jsonify({
                "message": "Account archived successfully",
                "account": AccountController._serialize(account),
            })

        except AuthorizationDenied as err:
            return jsonify({
                "message": str(err)
            }), 403