from flask import jsonify, request

from app.services.opportunity_oem_service import (
    OpportunityOEMService,
)


class OpportunityOEMController:

    @staticmethod
    def _serialize(association, active_role):
        oem = association.oem_partner

        result = {
            "opportunity_oem_id": (
                association.opportunity_oem_id
            ),
            "opportunity_id": (
                association.opportunity_id
            ),
            "oem_partner_id": (
                association.oem_partner_id
            ),
            "partner_name": oem.partner_name,
            "product_name": oem.product_name,
            "status": oem.status,
            "notes": oem.notes,
        }

        # Keep the same contact-data visibility rule
        # already used by the OEM registry.
        from app.constants.roles import (
            SALES_MANAGER,
            PRE_SALES_MANAGER,
        )

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
    def get_for_opportunity(
        opportunity_id,
        user,
        active_role,
    ):
        associations = (
            OpportunityOEMService.get_for_opportunity(
                opportunity_id,
                user,
                active_role,
            )
        )

        if associations is None:
            return jsonify({
                "message": "Opportunity not found"
            }), 404

        return jsonify([
            OpportunityOEMController._serialize(
                association,
                active_role,
            )
            for association in associations
        ]), 200

    @staticmethod
    def add_oem(
        opportunity_id,
        user,
        active_role,
    ):
        data = request.get_json() or {}

        oem_partner_id = data.get(
            "oem_partner_id"
        )

        if not oem_partner_id:
            return jsonify({
                "message": "oem_partner_id is required"
            }), 400

        try:
            association = (
                OpportunityOEMService.add_oem(
                    opportunity_id,
                    oem_partner_id,
                    user,
                    active_role,
                )
            )

            return jsonify({
                "message": "OEM Partner associated with opportunity",
                "opportunity_oem_id": (
                    association.opportunity_oem_id
                ),
            }), 201

        except LookupError as err:
            return jsonify({
                "message": str(err)
            }), 404

        except PermissionError as err:
            return jsonify({
                "message": str(err)
            }), 403

        except ValueError as err:
            return jsonify({
                "message": str(err)
            }), 409

    @staticmethod
    def remove_oem(
        opportunity_id,
        oem_partner_id,
        user,
        active_role,
    ):
        try:
            OpportunityOEMService.remove_oem(
                opportunity_id,
                oem_partner_id,
                user,
                active_role,
            )

            return jsonify({
                "message": "OEM Partner removed from opportunity"
            }), 200

        except LookupError as err:
            return jsonify({
                "message": str(err)
            }), 404

        except PermissionError as err:
            return jsonify({
                "message": str(err)
            }), 403
