from flask import jsonify

from app.schemas.stage_schema import StageResponseSchema
from app.services.stage_service import StageService

response_schema = StageResponseSchema()
response_list_schema = StageResponseSchema(many=True)


class StageController:

    @staticmethod
    def get_all():
        stages = StageService.get_all()
        return jsonify(response_list_schema.dump(stages)), 200

    @staticmethod
    def get(stage_id):
        stage = StageService.get_by_id(stage_id)

        if not stage:
            return jsonify({"message": "Stage not found"}), 404

        return jsonify(response_schema.dump(stage)), 200
