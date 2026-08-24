from flask import jsonify, request

from app.auth.authorization import AuthorizationDenied
from app.services.oem_service import OEMService


class OEMController:
    @staticmethod
    def get_all(user, active_role):
        oems = OEMService.get_all(user, active_role)
        return jsonify([
            {
                "oem_partner_id": oem.oem_partner_id,
                "account_id": oem.account_id,
                "partner_name": oem.partner_name,
                "product_name": oem.product_name,
                "contact_person": oem.contact_person,
                "email": oem.email,
                "phone": oem.phone,
                "status": oem.status,
                "notes": oem.notes,
            }
            for oem in oems
        ])

    @staticmethod
    def get_by_id(oem_id, user, active_role):
        oem = OEMService.get_by_id(oem_id, user, active_role)
        if not oem:
            return jsonify({"message": "OEM Partner not found"}), 404
        return jsonify({
            "oem_partner_id": oem.oem_partner_id,
            "account_id": oem.account_id,
            "partner_name": oem.partner_name,
            "product_name": oem.product_name,
            "contact_person": oem.contact_person,
            "email": oem.email,
            "phone": oem.phone,
            "status": oem.status,
            "notes": oem.notes,
        })

    @staticmethod
    def create(user, active_role):
        try:
            oem = OEMService.create(request.get_json() or {}, user, active_role)
            return jsonify({"message": "OEM Partner created", "id": oem.oem_partner_id}), 201
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 409

    @staticmethod
    def update(oem_id, user, active_role):
        try:
            OEMService.update(oem_id, request.get_json() or {}, user, active_role)
            return jsonify({"message": "OEM Partner updated"}), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

    @staticmethod
    def delete(oem_id, user, active_role):
        try:
            deleted = OEMService.delete(oem_id, user, active_role)
            if not deleted:
                return jsonify({"message": "OEM Partner not found"}), 404
            return jsonify({"message": "OEM Partner deleted"}), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
