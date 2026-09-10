from flask import jsonify, request

from app.auth.authorization import AuthorizationDenied
from app.constants.roles import (
    SALES_MANAGER,
    PRE_SALES_MANAGER,
)
from app.services.oem_service import OEMService


class OEMController:

    @staticmethod
    def _serialize(oem, active_role):
        result = {
            "oem_partner_id": oem.oem_partner_id,
            "account_id": oem.account_id,
            "partner_name": oem.partner_name,
            "product_name": oem.product_name,
            "status": oem.status,
            "notes": oem.notes,
        }

        if active_role in {
            SALES_MANAGER,
            PRE_SALES_MANAGER,
        }:
            result.update({
                "contact_person": oem.contact_person,
                "email": oem.email,
                "phone": oem.phone,
            })

        return result

    @staticmethod
    def get_all(user, active_role):
        oems = OEMService.get_all(
            user,
            active_role,
        )

        return jsonify([
            OEMController._serialize(
                oem,
                active_role,
            )
            for oem in oems
        ])

    @staticmethod
    def get_by_id(oem_id, user, active_role):
        oem = OEMService.get_by_id(
            oem_id,
            user,
            active_role,
        )

        if not oem:
            return jsonify({
                "message": "OEM Partner not found"
            }), 404

        return jsonify(
            OEMController._serialize(
                oem,
                active_role,
            )
        )

    @staticmethod
    def create(user, active_role):
        try:
            oem = OEMService.create(
                request.get_json() or {},
                user,
                active_role,
            )

            return jsonify({
                "message": "OEM Partner created",
                "id": oem.oem_partner_id,
            }), 201

        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

        except ValueError as err:
            return jsonify({"message": str(err)}), 400

    @staticmethod
    def update(oem_id, user, active_role):
        try:
            oem = OEMService.update(
                oem_id,
                request.get_json() or {},
                user,
                active_role,
            )

            if not oem:
                return jsonify({
                    "message": "OEM Partner not found"
                }), 404

            return jsonify({
                "message": "OEM Partner updated"
            }), 200

        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

        except ValueError as err:
            return jsonify({"message": str(err)}), 400

    @staticmethod
    def delete(oem_id, user, active_role):
        try:
            deleted = OEMService.delete(
                oem_id,
                user,
                active_role,
            )

            if not deleted:
                return jsonify({
                    "message": "OEM Partner not found"
                }), 404

            return jsonify({
                "message": "OEM Partner deleted"
            }), 200

        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
