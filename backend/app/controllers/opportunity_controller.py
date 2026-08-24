from flask import g, jsonify, request
from marshmallow import ValidationError

from app.auth.authorization import AuthorizationDenied
from app.schemas.opportunity_schema import (
    OpportunityCreateSchema,
    OpportunityResponseSchema,
    OpportunityUpdateSchema,
    StageHistoryResponseSchema,
    OpportunityReviewSchema,
    PreSalesAssignmentSchema,
    TechnicalStageTransitionSchema,
    OpportunityCloseSchema,
)
from app.services.opportunity_service import OpportunityService

create_schema = OpportunityCreateSchema()
update_schema = OpportunityUpdateSchema()
response_schema = OpportunityResponseSchema()
response_list_schema = OpportunityResponseSchema(many=True)
stage_history_schema = StageHistoryResponseSchema(many=True)
review_schema = OpportunityReviewSchema()


class OpportunityController:
    @staticmethod
    def create():
        try:
            data = create_schema.load(request.get_json() or {})
            opportunity = OpportunityService.create_opportunity(data, g.auth_user, g.active_role)
            return jsonify(response_schema.dump(opportunity)), 201
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to create opportunity"}), 500

    @staticmethod
    def get_all():
        opportunities = OpportunityService.get_all(g.auth_user, g.active_role)
        return jsonify(response_list_schema.dump(opportunities)), 200

    @staticmethod
    def get(opportunity_id):
        opportunity = OpportunityService.get_by_id(opportunity_id, g.auth_user, g.active_role)
        if not opportunity:
            return jsonify({"message": "Opportunity not found"}), 404
        return jsonify(response_schema.dump(opportunity)), 200

    @staticmethod
    def update(opportunity_id):
        try:
            data = update_schema.load(request.get_json() or {})
            opportunity = OpportunityService.update_opportunity(
                opportunity_id, data, g.auth_user, g.active_role
            )
            if not opportunity:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(opportunity)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 409
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to update opportunity"}), 500

    @staticmethod
    def pending_pre_sales_assignment():
        try:
            opportunities = OpportunityService.get_pending_pre_sales_assignment(
                g.auth_user, g.active_role
            )
            return jsonify(response_list_schema.dump(opportunities)), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

    @staticmethod
    def eligible_pre_sales_users(role):
        try:
            users = OpportunityService.get_eligible_pre_sales_users(
                g.auth_user, g.active_role, role
            )
            return jsonify([
                {"user_id": user.user_id, "full_name": user.full_name, "roles": user.role_names()}
                for user in users
            ]), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 400

    @staticmethod
    def finalize_pre_sales_assignment(opportunity_id):
        try:
            data = PreSalesAssignmentSchema().load(request.get_json() or {})
            opportunity = OpportunityService.finalize_pre_sales_assignment(
                opportunity_id=opportunity_id,
                solution_engineer_ids=data["solution_engineer_ids"],
                delivery_ids=data["delivery_ids"],
                updated_at=data["updated_at"],
                user=g.auth_user,
                active_role=g.active_role,
            )
            if not opportunity:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(opportunity)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 400
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to finalize technical assignment"}), 500

    @staticmethod
    def get_technical_team(opportunity_id):
        opportunity = OpportunityService.get_by_id(
            opportunity_id, g.auth_user, g.active_role
        )
        if not opportunity:
            return jsonify({"message": "Opportunity not found"}), 404
        return jsonify({
            "opportunity_id": opportunity.opportunity_id,
            "sales_owner": opportunity.sales_owner.full_name if opportunity.sales_owner else None,
            "solution_engineers": [
                {"team_id": member.team_id, "user_id": member.user_id, "full_name": member.user.full_name}
                for member in opportunity.team_members
                if member.role == "Solution Engineer"
            ],
        }), 200

    @staticmethod
    def get_stage_history(opportunity_id):
        history = OpportunityService.get_stage_history(
            opportunity_id,
            g.auth_user,
            g.active_role,
        )
        if history is None:
            return jsonify({"message": "Opportunity not found"}), 404
        return jsonify(stage_history_schema.dump(history)), 200

    @staticmethod
    def qualify(opportunity_id):
        try:
            opportunity = OpportunityService.qualify_opportunity(
                opportunity_id, g.auth_user, g.active_role
            )
            if not opportunity:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(opportunity)), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 400
        except Exception:
            return jsonify({"message": "Failed to qualify opportunity"}), 500

    @staticmethod
    def submit_for_review(opportunity_id):
        try:
            opportunity = OpportunityService.submit_for_sales_manager_review(
                opportunity_id, g.auth_user, g.active_role
            )
            if not opportunity:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(opportunity)), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except Exception:
            return jsonify({"message": "Failed to submit opportunity for review"}), 500

    @staticmethod
    def pending_review():
        try:
            opportunities = OpportunityService.get_pending_review(
                g.auth_user, g.active_role
            )
            return jsonify(response_list_schema.dump(opportunities)), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

    @staticmethod
    def eligible_sales_owners():
        try:
            users = OpportunityService.get_eligible_sales_owners(
                g.auth_user, g.active_role
            )
            return jsonify([
                {"user_id": user.user_id, "full_name": user.full_name}
                for user in users
            ]), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

    @staticmethod
    def review(opportunity_id):
        try:
            data = review_schema.load(request.get_json() or {})
            opportunity = OpportunityService.review_opportunity(
                opportunity_id=opportunity_id,
                decision=data["decision"],
                sales_owner_id=data.get("sales_owner_id"),
                reason=data.get("reason"),
                updated_at=data["updated_at"],
                user=g.auth_user,
                active_role=g.active_role,
            )
            if not opportunity:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(opportunity)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 400
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to review opportunity"}), 500

    @staticmethod
    def transition_technical_stage(opportunity_id):
        try:
            data = TechnicalStageTransitionSchema().load(request.get_json() or {})
            from app.services.stage_service import StageService
            opportunity = StageService.transition_technical_stage(
                opportunity_id, data["target_stage"], data["updated_at"],
                data.get("remarks"), g.auth_user, g.active_role,
            )
            if not opportunity:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(opportunity)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 400
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to change technical stage"}), 500

    @staticmethod
    def close(opportunity_id, won):
        try:
            data = OpportunityCloseSchema().load(request.get_json() or {})
            from app.services.stage_service import StageService
            opportunity = StageService.close_opportunity(
                opportunity_id, won, data.get("reason"), data["updated_at"],
                g.auth_user, g.active_role,
            )
            if not opportunity:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify(response_schema.dump(opportunity)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 400
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to close opportunity"}), 500

    @staticmethod
    def delete(opportunity_id):
        try:
            deleted = OpportunityService.delete_opportunity(
                opportunity_id, g.auth_user, g.active_role
            )
            if not deleted:
                return jsonify({"message": "Opportunity not found"}), 404
            return jsonify({"message": "Opportunity deleted"}), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except Exception:
            return jsonify({"message": "Failed to delete opportunity"}), 500
