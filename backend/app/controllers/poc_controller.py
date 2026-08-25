from flask import g, jsonify, request
from marshmallow import ValidationError

from app.auth.authorization import AuthorizationDenied
from app.schemas.poc_schema import (
    PocRequestSchema, PocResponseSchema, PocApprovalSchema, PocRejectionSchema,
    PocDesignUpdateSchema, PocExecutionStartSchema, PocResultSchema, PocCompleteSchema,
)
from app.services.poc_service import PocService

response_schema = PocResponseSchema()
response_list_schema = PocResponseSchema(many=True)


class PocController:
    @staticmethod
    def request():
        try:
            data = PocRequestSchema().load(request.get_json() or {})
            poc = PocService.request_poc(data, g.auth_user, g.active_role)
            return jsonify(response_schema.dump(poc)), 201
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except ValueError as err:
            return jsonify({"message": str(err)}), 400
        except Exception as err:
            import traceback
            traceback.print_exc()
            return jsonify({"message": str(err)}), 500

    @staticmethod
    def get(poc_id):
        poc = PocService.get_by_id(poc_id, g.auth_user, g.active_role)
        if not poc:
            return jsonify({"message": "POC not found"}), 404
        return jsonify(response_schema.dump(poc)), 200

    @staticmethod
    def get_by_opportunity(opportunity_id):
        pocs = PocService.get_by_opportunity(opportunity_id, g.auth_user, g.active_role)
        return jsonify(response_list_schema.dump(pocs)), 200

    @staticmethod
    def pending_approval():
        try:
            pocs = PocService.get_pending_approval(g.auth_user, g.active_role)
            return jsonify(response_list_schema.dump(pocs)), 200
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

    @staticmethod
    def update_design(poc_id):
        try:
            data = PocDesignUpdateSchema().load(request.get_json() or {})
            poc = PocService.update_design(poc_id, data, g.auth_user, g.active_role)
            if not poc:
                return jsonify({"message": "POC not found"}), 404
            return jsonify(response_schema.dump(poc)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to update POC design"}), 500

    @staticmethod
    def approve(poc_id):
        try:
            data = PocApprovalSchema().load(request.get_json() or {})
            poc = PocService.approve_poc(poc_id, data["updated_at"], g.auth_user, g.active_role)
            if not poc:
                return jsonify({"message": "POC not found"}), 404
            return jsonify(response_schema.dump(poc)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except (ValueError, RuntimeError) as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to approve POC"}), 500

    @staticmethod
    def reject(poc_id):
        try:
            data = PocRejectionSchema().load(request.get_json() or {})
            poc = PocService.reject_poc(poc_id, data["reason"], data["updated_at"], g.auth_user, g.active_role)
            if not poc:
                return jsonify({"message": "POC not found"}), 404
            return jsonify(response_schema.dump(poc)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except (ValueError, RuntimeError) as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to reject POC"}), 500

    @staticmethod
    def start_execution(poc_id):
        try:
            data = PocExecutionStartSchema().load(request.get_json() or {})
            poc = PocService.start_execution(poc_id, data["updated_at"], g.auth_user, g.active_role)
            if not poc:
                return jsonify({"message": "POC not found"}), 404
            return jsonify(response_schema.dump(poc)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to start POC execution"}), 500

    @staticmethod
    def submit_result(poc_id):
        try:
            data = PocResultSchema().load(request.get_json() or {})
            poc = PocService.submit_result(poc_id, data, g.auth_user, g.active_role)
            if not poc:
                return jsonify({"message": "POC not found"}), 404
            return jsonify(response_schema.dump(poc)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except (ValueError, RuntimeError) as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to submit POC result"}), 500

    @staticmethod
    def complete(poc_id):
        try:
            data = PocCompleteSchema().load(request.get_json() or {})
            poc = PocService.complete_poc(poc_id, data["updated_at"], g.auth_user, g.active_role)
            if not poc:
                return jsonify({"message": "POC not found"}), 404
            return jsonify(response_schema.dump(poc)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409
        except Exception:
            return jsonify({"message": "Failed to complete POC"}), 500

    @staticmethod
    def delete(poc_id):
        try:
            PocService.delete_poc(poc_id, g.auth_user, g.active_role)
            return jsonify({"message": "POCs cannot be deleted"}), 403
        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403
