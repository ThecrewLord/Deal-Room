from flask import g, jsonify, request
from marshmallow import ValidationError

from app.auth.authorization import AuthorizationDenied
from app.schemas.stakeholder_schema import (
    StakeholderCreateSchema,
    StakeholderResponseSchema,
    StakeholderUpdateSchema,
)
from app.services.stakeholder_service import StakeholderService

create_schema = StakeholderCreateSchema()
update_schema = StakeholderUpdateSchema()
response_schema = StakeholderResponseSchema()
response_list_schema = StakeholderResponseSchema(many=True)


class StakeholderController:
    @staticmethod
    def create():
        try:
            data = create_schema.load(request.get_json() or {})
            stakeholder = StakeholderService.create_stakeholder(data, g.auth_user, g.active_role)
            return jsonify(response_schema.dump(stakeholder)), 201
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except Exception:
            return jsonify({"message": "Failed to create stakeholder"}), 500

    @staticmethod
    def get(stakeholder_id):
        stakeholder = StakeholderService.get_by_id(stakeholder_id, g.auth_user, g.active_role)
        if not stakeholder:
            return jsonify({"message": "Stakeholder not found"}), 404
        return jsonify(response_schema.dump(stakeholder)), 200

    @staticmethod
    def get_by_opportunity(opportunity_id):
        stakeholders = StakeholderService.get_by_opportunity(
            opportunity_id, g.auth_user, g.active_role
        )
        return jsonify(response_list_schema.dump(stakeholders)), 200

    @staticmethod
    def update(stakeholder_id):
        try:
            data = update_schema.load(request.get_json() or {})
            stakeholder = StakeholderService.update_stakeholder(
                stakeholder_id, data, g.auth_user, g.active_role
            )
            if not stakeholder:
                return jsonify({"message": "Stakeholder not found"}), 404
            return jsonify(response_schema.dump(stakeholder)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to update stakeholder"}), 500

    @staticmethod
    def delete(stakeholder_id):
        try:
            deleted = StakeholderService.delete_stakeholder(
                stakeholder_id, g.auth_user, g.active_role
            )
            if not deleted:
                return jsonify({"message": "Stakeholder not found"}), 404
            return jsonify({"message": "Stakeholder deleted"}), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except Exception:
            return jsonify({"message": "Failed to delete stakeholder"}), 500
