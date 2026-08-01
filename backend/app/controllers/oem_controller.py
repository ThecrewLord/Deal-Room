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

        try:
            oem = OEMService.create(request.get_json())

            return (
                jsonify(
                    {
                        "message": "OEM Partner created",
                        "id": oem.oem_partner_id,
                    }
                ),
                201,
            )

        except ValueError as err:
            return jsonify(
                {"message": str(err)}
            ), 409

        except Exception:
            return jsonify(
                {
                    "message": "Failed to create OEM Partner"
                }
            ), 500

    @staticmethod
    def update(oem_id):

        try:
            oem = OEMService.update(
                oem_id,
                request.get_json(),
            )

            if not oem:
                return jsonify(
                    {
                        "message": "OEM Partner not found"
                    }
                ), 404

            return jsonify(
                {
                    "message": "OEM Partner updated"
                }
            ), 200

        except ValueError as err:
            return jsonify(
                {"message": str(err)}
            ), 409

        except Exception:
            return jsonify(
                {
                    "message": "Failed to update OEM Partner"
                }
            ), 500

    @staticmethod
    def delete(oem_id):

        try:
            deleted = OEMService.delete(oem_id)

            if not deleted:
                return jsonify(
                    {
                        "message": "OEM Partner not found"
                    }
                ), 404

            return jsonify(
                {
                    "message": "OEM Partner deleted"
                }
            ), 200

        except Exception:
            return jsonify(
                {
                    "message": "Failed to delete OEM Partner"
                }
            ), 500
