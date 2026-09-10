from flask import jsonify, request
from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.services.oem_service import OEMService
def serialize(o,user,role):
    d={"oem_partner_id":o.oem_partner_id,"account_id":o.account_id,"partner_name":o.partner_name,"product_name":o.product_name,"status":o.status}
    if role=="Leadership": d.update(contact_person=o.contact_person,email=o.email,phone=o.phone,notes=o.notes)
    return d
class OEMController:
    @staticmethod
    def get_all(user,active_role): return jsonify([serialize(o,user,active_role) for o in OEMService.get_all(user,active_role)])
    @staticmethod
    def get_by_id(oem_id,user,active_role):
        o=OEMService.get_by_id(oem_id,user,active_role); return (jsonify(serialize(o,user,active_role)),200) if o else (jsonify({"message":"OEM Partner not found"}),404)
    @staticmethod
    def create(user,active_role):
        try: return jsonify(serialize(OEMService.create(request.get_json() or {},user,active_role),user,active_role)),201
        except AuthorizationDenied as e: return jsonify({"message":str(e)}),403
        except ValueError as e: return jsonify({"message":str(e)}),409
    @staticmethod
    def update(oem_id,user,active_role):
        try:
            o=OEMService.update(oem_id,request.get_json() or {},user,active_role)
            return (jsonify(serialize(o,user,active_role)),200) if o else (jsonify({"message":"OEM Partner not found"}),404)
        except AuthorizationDenied as e: return jsonify({"message":str(e)}),403
        except ValueError as e: return jsonify({"message":str(e)}),409
    @staticmethod
    def delete(oem_id,user,active_role):
        try: return jsonify({"message":"OEM Partner deleted"}) if OEMService.delete(oem_id,user,active_role) else (jsonify({"message":"OEM Partner not found"}),404)
        except AuthorizationDenied as e: return jsonify({"message":str(e)}),403
        except ValueError as e: return jsonify({"message":str(e)}),409
