from flask import jsonify, request, g
from marshmallow import ValidationError
from app.auth.authorization import AuthorizationDenied
from app.schemas.account_schema import AccountCreateSchema
from app.services.account_service import AccountService
schema=AccountCreateSchema()
def payload(a):
    return {"account_id":a.account_id,"account_name":a.account_name,"canonical_name":a.canonical_name,"status":a.status,
            "industry":a.industry,"website":a.website,"phone":a.phone,"country":a.country,"state":a.state,"city":a.city,"address":a.address}
class AccountController:
    @staticmethod
    def get_all(user, active_role): return jsonify([payload(a) for a in AccountService.get_all(user,active_role)])
    @staticmethod
    def get(account_id,user,active_role):
        a=AccountService.get_by_id(account_id,user,active_role)
        return (jsonify(payload(a)),200) if a else (jsonify({"message":"Account not found"}),404)
    @staticmethod
    def create(user,active_role):
        try: return jsonify(payload(AccountService.create(request.get_json() or {},user,active_role))),201
        except ValidationError as e: return jsonify(e.messages),400
        except AuthorizationDenied as e: return jsonify({"message":str(e)}),403
        except ValueError as e: return jsonify({"message":str(e)}),409
    @staticmethod
    def archive(account_id,user,active_role):
        try: return jsonify(payload(AccountService.archive(account_id,user,active_role))),200
        except AuthorizationDenied as e: return jsonify({"message":str(e)}),403
        except ValueError as e: return jsonify({"message":str(e)}),409
    @staticmethod
    def ban(account_id,user,active_role):
        try: return jsonify(payload(AccountService.ban(account_id,user,active_role))),200
        except AuthorizationDenied as e: return jsonify({"message":str(e)}),403
        except ValueError as e: return jsonify({"message":str(e)}),409
    @staticmethod
    def delete_duplicate(account_id,user,active_role):
        try: AccountService.delete_duplicate(account_id,user,active_role); return jsonify({"message":"Account deleted"}),200
        except AuthorizationDenied as e: return jsonify({"message":str(e)}),403
        except ValueError as e: return jsonify({"message":str(e)}),409
