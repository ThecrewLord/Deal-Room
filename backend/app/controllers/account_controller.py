from flask import request, jsonify
from marshmallow import ValidationError

from app.schemas.account_schema import (
    AccountCreateSchema,
    AccountUpdateSchema,
    AccountResponseSchema,
)
from app.services.account_service import AccountService

create_schema = AccountCreateSchema()
update_schema = AccountUpdateSchema()
response_schema = AccountResponseSchema()
response_list_schema = AccountResponseSchema(many=True)


class AccountController:

    @staticmethod
    def create():
        try:
            data = create_schema.load(request.get_json())
            account = AccountService.create_account(data)
            return jsonify(response_schema.dump(account)), 201

        except ValidationError as err:
            return jsonify(err.messages), 400

        except ValueError as err:
            return jsonify({"message": str(err)}), 409

        except Exception:
            return jsonify({"message": "Failed to create account"}), 500

    @staticmethod
    def get_all():
        accounts = AccountService.get_all()
        return jsonify(response_list_schema.dump(accounts)), 200

    @staticmethod
    def get(account_id):
        account = AccountService.get_by_id(account_id)

        if not account:
            return jsonify({"message": "Account not found"}), 404

        return jsonify(response_schema.dump(account)), 200

    @staticmethod
    def update(account_id):
        try:
            data = update_schema.load(request.get_json())
            account = AccountService.update_account(account_id, data)

            if not account:
                return jsonify({"message": "Account not found"}), 404

            return jsonify(response_schema.dump(account)), 200

        except ValidationError as err:
            return jsonify(err.messages), 400

        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409

        except Exception:
            return jsonify({"message": "Failed to update account"}), 500

    @staticmethod
    def delete(account_id):
        try:
            deleted = AccountService.delete_account(account_id)

            if not deleted:
                return jsonify({"message": "Account not found"}), 404

            return jsonify({"message": "Account deleted"}), 200

        except Exception:
            return jsonify({"message": "Failed to delete account"}), 500
