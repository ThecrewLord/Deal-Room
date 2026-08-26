from flask import g, jsonify, request
from marshmallow import ValidationError
from app.auth.authorization import AuthorizationDenied
from app.schemas.solution_design_schema import SolutionDesignUpdateSchema, SolutionDesignResponseSchema
from app.services.solution_design_service import SolutionDesignService

response_schema = SolutionDesignResponseSchema()

class SolutionDesignController:
    @staticmethod
    def get(opportunity_id):
        design = SolutionDesignService.get(opportunity_id, g.auth_user, g.active_role)
        if design is None:
            return jsonify({"message": "Solution design not found"}), 404
        return jsonify(response_schema.dump(design)), 200

    @staticmethod
    def update(opportunity_id):
        try:
            data = SolutionDesignUpdateSchema().load(request.get_json() or {})
            design = SolutionDesignService.update(opportunity_id, data, g.auth_user, g.active_role)
            if design is None:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(design)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to update technical design"}), 500
