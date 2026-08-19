from flask import request, jsonify
from marshmallow import ValidationError

from app.schemas.poc_schema import (
    PocCreateSchema,
    PocUpdateSchema,
    PocResponseSchema,
)
from app.services.poc_service import PocService

create_schema = PocCreateSchema()
update_schema = PocUpdateSchema()
response_schema = PocResponseSchema()
response_list_schema = PocResponseSchema(many=True)


class PocController:

    @staticmethod
    def create():
        try:
            data = create_schema.load(request.get_json())
            poc = PocService.create_poc(data)
            return jsonify(response_schema.dump(poc)), 201

        except ValidationError as err:
            return jsonify(err.messages), 400

        except Exception as e:
            return jsonify({"message": str(e)}), 500

    @staticmethod
    def get(poc_id):
        poc = PocService.get_by_id(poc_id)

        if not poc:
            return jsonify({"message": "POC not found"}), 404

        return jsonify(response_schema.dump(poc)), 200

    @staticmethod
    def get_by_opportunity(opportunity_id):
        pocs = PocService.get_by_opportunity(opportunity_id)
        return jsonify(response_list_schema.dump(pocs)), 200

    @staticmethod
    def update(poc_id):
        try:
            data = update_schema.load(request.get_json())
            poc = PocService.update_poc(poc_id, data)

            if not poc:
                return jsonify({"message": "POC not found"}), 404

            return jsonify(response_schema.dump(poc)), 200

        except ValidationError as err:
            return jsonify(err.messages), 400

        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409

        except Exception:
            return jsonify({"message": "Failed to update POC"}), 500

    @staticmethod
    def delete(poc_id):
        try:
            deleted = PocService.delete_poc(poc_id)

            if not deleted:
                return jsonify({"message": "POC not found"}), 404

            return jsonify({"message": "POC deleted"}), 200

        except Exception:
            return jsonify({"message": "Failed to delete POC"}), 500
