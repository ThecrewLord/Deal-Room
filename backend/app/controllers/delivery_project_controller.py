from flask import g, jsonify, request
from app.services.delivery_dashboard_service import DeliveryDashboardService
from app.auth.authorization import AuthorizationService

from app.repositories.delivery_project_repository import (
    DeliveryProjectRepository,
)

from app.services.delivery_project_service import (
    DeliveryProjectService,
)

from app.services.delivery_assignment_service import (
    DeliveryAssignmentService,
)


class DeliveryProjectController:

    # ================================================================
    # CREATE PROJECT
    # ================================================================
    @staticmethod
    def get_dashboard():
        try:
            dashboard = DeliveryDashboardService.get_dashboard(
                user=g.auth_user,
                active_role=g.active_role,
            )
            return jsonify(dashboard), 200

        except ValueError as err:
            return jsonify({"message": str(err)}), 403

        except Exception as err:
            import traceback
            traceback.print_exc()
            return jsonify({
                "message": "Failed to load delivery dashboard.",
                "detail": str(err),
            }), 500

    @staticmethod
    def get_pending_assignments():
        if not AuthorizationService.can_view_pending_delivery_assignments(
            g.auth_user,
            g.active_role,
        ):
            return jsonify({
                "message": "Only a Delivery Manager can view pending delivery assignments."
            }), 403

        pending = DeliveryProjectRepository.get_pending_poc_assignments()

        return jsonify({
            "count": len(pending),
            "items": [
                {
                    "poc_id": poc.poc_id,
                    "opportunity_id": poc.opportunity_id,
                    "poc_name": poc.poc_name,
                    "status": poc.status,
                    "start_date": (
                        poc.start_date.isoformat()
                        if poc.start_date else None
                    ),
                    "end_date": (
                        poc.end_date.isoformat()
                        if poc.end_date else None
                    ),
                    "target_date": (
                        poc.target_date.isoformat()
                        if poc.target_date else None
                    ),
                    "objective": poc.objective,
                    "success_metric": poc.success_metric,
                    "failure_condition": poc.failure_condition,
                    "requested_by": poc.requested_by,
                    "submitted_by": poc.submitted_by,
                    "submitted_at": (
                        poc.submitted_at.isoformat()
                        if poc.submitted_at else None
                    ),
                }
                for poc in pending
            ],
        }), 200


    @staticmethod
    def get_candidates():
        if not AuthorizationService.can_view_delivery_candidates(
            g.auth_user,
            g.active_role,
        ):
            return jsonify({
                "message": (
                    "Only a Delivery Manager can view "
                    "delivery team candidates."
                )
            }), 403

        candidates = DeliveryAssignmentService.get_candidates()

        return jsonify({
            "count": len(candidates),
            "items": candidates,
        }), 200

    @staticmethod
    def create_project():
        try:
            data = request.get_json() or {}

            opportunity_id = data.get(
                "opportunity_id"
            )

            poc_id = data.get(
                "poc_id"
            )

            project_name = data.get(
                "project_name"
            )

            start_date = data.get(
                "start_date"
            )

            target_date = data.get(
                "target_date"
            )

            if not opportunity_id:
                return jsonify({
                    "message": (
                        "opportunity_id is required."
                    )
                }), 400

            if not poc_id:
                return jsonify({
                    "message": (
                        "poc_id is required."
                    )
                }), 400

            if not project_name:
                return jsonify({
                    "message": (
                        "project_name is required."
                    )
                }), 400

            print(
                "\nDEBUG DELIVERY AUTH:",
                "user=", g.auth_user.email,
                "user_id=", g.auth_user.user_id,
                "active_role=", repr(g.active_role),
            )

            project = (
                DeliveryProjectService.create_project(
                    opportunity_id=opportunity_id,
                    poc_id=poc_id,
                    project_name=project_name,
                    created_by=g.auth_user.user_id,
                    active_role=g.active_role,
                    start_date=start_date,
                    target_date=target_date,
                )
            )

            return jsonify(
                DeliveryProjectController
                ._serialize_project(project)
            ), 201

        except ValueError as err:

            return jsonify({
                "message": str(err)
            }), 400

        except Exception as err:

            import traceback
            traceback.print_exc()

            return jsonify({
                "message": (
                    "Failed to create delivery project."
                ),
                "detail": str(err),
            }), 500

    # ================================================================
    # UPDATE PROJECT STATUS
    # ================================================================

    @staticmethod
    def update_status(project_id):
        try:
            data = request.get_json() or {}

            new_status = data.get("status")

            if not new_status:
                return jsonify({
                    "message": "status is required."
                }), 400

            project = DeliveryProjectService.transition_status(
                project_id=project_id,
                new_status=new_status,
                user_id=g.auth_user.user_id,
                active_role=g.active_role,
            )

            return jsonify(
                DeliveryProjectController._serialize_project(project)
            ), 200

        except ValueError as err:
            return jsonify({
                "message": str(err)
            }), 400

        except Exception as err:
            import traceback
            traceback.print_exc()

            return jsonify({
                "message": "Failed to update delivery project status.",
                "detail": str(err),
            }), 500


    # ================================================================
    # GET PROJECT
    # ================================================================

    @staticmethod
    def get_project(project_id):
        try:

            project = (
                DeliveryProjectRepository
                .get_by_id(project_id)
            )

            if not project:
                return jsonify({
                    "message": (
                        "Delivery project not found."
                    )
                }), 404

            # ------------------------------------------------------------
            # Delivery project visibility
            # ------------------------------------------------------------

            if not AuthorizationService.can_view_delivery_project(
                g.auth_user,
                g.active_role,
                project,
            ):
                return jsonify({
                    "message": (
                        "You are not authorized to view this delivery project."
                    )
                }), 403

            assignments = (
                DeliveryAssignmentService
                .get_assignments(project_id)
            )

            response = (
                DeliveryProjectController
                ._serialize_project(project)
            )

            response["assignments"] = [
                {
                    "assignment_id": assignment.assignment_id,
                    "project_id": assignment.project_id,
                    "user_id": assignment.user_id,
                    "assigned_by": assignment.assigned_by,
                    "role": assignment.role,
                    "is_active": assignment.is_active,
                    "assigned_at": (
                        assignment.assigned_at.isoformat()
                        if assignment.assigned_at
                        else None
                    ),
                    "user_name": (
                        assignment.user.full_name
                        if assignment.user
                        else None
                    ),
                }
                for assignment in assignments
            ]

            return jsonify(response), 200

        except ValueError as err:

            return jsonify({
                "message": str(err)
            }), 400

        except Exception as err:

            import traceback
            traceback.print_exc()

            return jsonify({
                "message": (
                    "Failed to retrieve delivery project."
                ),
                "detail": str(err),
            }), 500

    # ================================================================
    # ASSIGN TEAM MEMBER
    # ================================================================

    @staticmethod
    def assign_member(project_id):
        try:

            data = request.get_json() or {}

            user_id = data.get(
                "user_id"
            )

            role = data.get(
                "role"
            )

            if not user_id:
                return jsonify({
                    "message": (
                        "user_id is required."
                    )
                }), 400

            if not role:
                return jsonify({
                    "message": (
                        "role is required."
                    )
                }), 400

            assignment = (
                DeliveryAssignmentService.assign(
                    project_id=project_id,
                    user_id=user_id,
                    role=role,
                    assigned_by=g.auth_user.user_id,
                    active_role=g.active_role,
                )
            )

            return jsonify({
                "assignment_id": assignment.assignment_id,
                "project_id": assignment.project_id,
                "user_id": assignment.user_id,
                "assigned_by": assignment.assigned_by,
                "role": assignment.role,
                "is_active": assignment.is_active,
                "assigned_at": (
                    assignment.assigned_at.isoformat()
                    if assignment.assigned_at
                    else None
                ),
            }), 201

        except ValueError as err:

            return jsonify({
                "message": str(err)
            }), 400

        except Exception as err:

            import traceback
            traceback.print_exc()

            return jsonify({
                "message": (
                    "Failed to assign delivery "
                    "team member."
                ),
                "detail": str(err),
            }), 500

    # ================================================================
    # GET ASSIGNMENTS
    # ================================================================

    @staticmethod
    def get_assignments(project_id):
        try:

            project = (
                DeliveryProjectRepository
                .get_by_id(project_id)
            )

            if not project:
                return jsonify({
                    "message": (
                        "Delivery project not found."
                    )
                }), 404

            # ------------------------------------------------------------
            # Delivery project visibility
            # ------------------------------------------------------------

            if not AuthorizationService.can_view_delivery_project(
                g.auth_user,
                g.active_role,
                project,
            ):
                return jsonify({
                    "message": (
                        "You are not authorized to view this delivery project."
                    )
                }), 403

            assignments = (
                DeliveryAssignmentService
                .get_assignments(project_id)
            )

            return jsonify([
                {
                    "assignment_id": assignment.assignment_id,
                    "project_id": assignment.project_id,
                    "user_id": assignment.user_id,
                    "assigned_by": assignment.assigned_by,
                    "role": assignment.role,
                    "is_active": assignment.is_active,
                    "assigned_at": (
                        assignment.assigned_at.isoformat()
                        if assignment.assigned_at
                        else None
                    ),
                    "user_name": (
                        assignment.user.full_name
                        if assignment.user
                        else None
                    ),
                }
                for assignment in assignments
            ]), 200

        except ValueError as err:

            return jsonify({
                "message": str(err)
            }), 400

        except Exception as err:

            import traceback
            traceback.print_exc()

            return jsonify({
                "message": (
                    "Failed to retrieve delivery "
                    "assignments."
                ),
                "detail": str(err),
            }), 500

    # ================================================================
    # REMOVE ASSIGNMENT
    # ================================================================

    @staticmethod
    def remove_member(
        project_id,
        user_id,
    ):
        try:

            assignment = (
                DeliveryAssignmentService
                .remove_assignment(
                    project_id=project_id,
                    user_id=user_id,
                    removed_by=g.auth_user.user_id,
                    active_role=g.active_role,
                )
            )

            return jsonify({
                "message": (
                    "Delivery team member removed."
                ),
                "assignment_id": (
                    assignment.assignment_id
                ),
                "project_id": (
                    assignment.project_id
                ),
                "user_id": (
                    assignment.user_id
                ),
                "is_active": (
                    assignment.is_active
                ),
            }), 200

        except ValueError as err:

            return jsonify({
                "message": str(err)
            }), 400

        except Exception as err:

            import traceback
            traceback.print_exc()

            return jsonify({
                "message": (
                    "Failed to remove delivery "
                    "team member."
                ),
                "detail": str(err),
            }), 500

    # ================================================================
    # SERIALIZER
    # ================================================================

    @staticmethod
    def _serialize_project(project):

        return {
            "project_id": project.project_id,
            "opportunity_id": project.opportunity_id,
            "poc_id": project.poc_id,
            "project_name": project.project_name,
            "status": project.status,
            "start_date": (
                project.start_date.isoformat()
                if project.start_date
                else None
            ),
            "target_date": (
                project.target_date.isoformat()
                if project.target_date
                else None
            ),
            "created_by": project.created_by,
            "created_at": (
                project.created_at.isoformat()
                if project.created_at
                else None
            ),
            "updated_at": (
                project.updated_at.isoformat()
                if project.updated_at
                else None
            ),
        }
