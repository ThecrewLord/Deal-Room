from flask import jsonify

from app.services.account_service import AccountService


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
