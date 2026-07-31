from flask import jsonify, request

from app.services.oem_service import OEMService


class OEMController:

    @staticmethod
    def get_all():
        oems = OEMService.get_all()

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
    def get_by_id(oem_id):
        oem = OEMService.get_by_id(oem_id)

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
    def create():
        oem = OEMService.create(request.get_json())

        return jsonify({
            "message": "OEM Partner created",
            "id": oem.oem_partner_id
        }), 201

    @staticmethod
    def update(oem_id):
        oem = OEMService.update(oem_id, request.get_json())

        if not oem:
            return jsonify({"message": "OEM Partner not found"}), 404

        return jsonify({"message": "OEM Partner updated"})

    @staticmethod
    def delete(oem_id):
        deleted = OEMService.delete(oem_id)

        if not deleted:
            return jsonify({"message": "OEM Partner not found"}), 404

        return jsonify({"message": "OEM Partner deleted"})