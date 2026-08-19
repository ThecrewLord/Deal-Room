from flask import request, jsonify
from marshmallow import ValidationError
from app.schemas.opportunity_schema import (
    OpportunityCreateSchema,
    OpportunityUpdateSchema,
    OpportunityResponseSchema,
)
from app.schemas.opportunity_schema import (
    OpportunityCreateSchema,
    OpportunityResponseSchema,
)

from app.services.opportunity_service import (
    OpportunityService,
)

create_schema = OpportunityCreateSchema()
update_schema = OpportunityUpdateSchema()
response_schema = OpportunityResponseSchema()

response_list_schema = OpportunityResponseSchema(
    many=True
)


class OpportunityController:

    @staticmethod
    def create():
        try:
            data = create_schema.load(request.get_json())

            opportunity = OpportunityService.create_opportunity(data)

            return (
                jsonify(response_schema.dump(opportunity)),
                201,
            )

        except ValidationError as err:
            return jsonify(err.messages), 400

        except ValueError as err:
            return jsonify({"message": str(err)}), 409

        except Exception:
            return (
                jsonify(
                    {
                        "message": "Failed to create opportunity"
                    }
                ),
                500,
            )

        try:
            data = create_schema.load(
                request.get_json()
            )

        except ValidationError as err:

            return (
                jsonify(err.messages),
                400,
            )

        opportunity = OpportunityService.create_opportunity(
            data
        )

        return (
            jsonify(
                response_schema.dump(opportunity)
            ),
            201,
        )

        data = create_schema.load(
            request.get_json()
        )

        opportunity = (
            OpportunityService.create_opportunity(
                data
            )
        )

        return (
            jsonify(
                response_schema.dump(
                    opportunity
                )
            ),
            201,
        )

    @staticmethod
    def get_all():

        opportunities = (
            OpportunityService.get_all()
        )

        return (
            jsonify(
                response_list_schema.dump(
                    opportunities
                )
            ),
            200,
        )

    @staticmethod
    def get(opportunity_id):

        opportunity = (
            OpportunityService.get_by_id(
                opportunity_id
            )
        )

        if not opportunity:

            return (
                jsonify(
                    {
                        "message":
                        "Opportunity not found"
                    }
                ),
                404,
            )

        return (
            jsonify(
                response_schema.dump(
                    opportunity
                )
            ),
            200,
        )

    @staticmethod
    def update(opportunity_id):

        try:
            data = update_schema.load(request.get_json())

            opportunity = OpportunityService.update_opportunity(
                opportunity_id,
                data,
            )

            if not opportunity:
                return (
                    jsonify(
                        {
                            "message": "Opportunity not found"
                        }
                    ),
                    404,
                )

            return (
                jsonify(response_schema.dump(opportunity)),
                200,
            )

        except ValidationError as err:
            return jsonify(err.messages), 400

        except ValueError as err:
            return jsonify({"message": str(err)}), 409

        except RuntimeError as err:
            return jsonify(
                {
                    "message": str(err)
                }
            ), 409

        except Exception:
            return (
                jsonify(
                    {
                        "message": "Failed to update opportunity"
                    }
                ),
                500,
            )


    @staticmethod

    def delete(opportunity_id):

        try:

            deleted = OpportunityService.delete_opportunity(
                opportunity_id
            )

            if not deleted:
                return (
                    jsonify(
                        {
                            "message": "Opportunity not found"
                        }
                    ),
                    404,
                )

            return (
                jsonify(
                    {
                        "message": "Opportunity deleted"
                    }
                ),
                200,
            )

        except Exception:
            return (
                jsonify(
                    {
                        "message": "Failed to delete opportunity"
                    }
                ),
                500,
            )

        deleted = (
            OpportunityService.delete_opportunity(
                opportunity_id
            )
        )

        if not deleted:

            return (
                jsonify(
                    {
                        "message":
                        "Opportunity not found"
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "message":
                    "Opportunity deleted"
                }
            ),
            200,
        )
    @staticmethod
    def search():
        search_term = request.args.get("q", "").strip()

        if not search_term:
            return jsonify({
                "message": "Search term is required"
            }), 400

        opportunities = OpportunityService.search(search_term)

        return (
            jsonify(
                response_list_schema.dump(opportunities)
            ),
            200,
        )