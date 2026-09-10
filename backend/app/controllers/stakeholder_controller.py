from flask import g, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import traceback

from app.auth.authorization import AuthorizationDenied
from app.schemas.stakeholder_schema import (
    StakeholderCreateSchema,
    StakeholderResponseSchema,
    StakeholderUpdateSchema,
    StakeholderTagCreateSchema,
    StakeholderTagResponseSchema,
)
from app.services.stakeholder_service import StakeholderService


create_schema = StakeholderCreateSchema()
update_schema = StakeholderUpdateSchema()
response_schema = StakeholderResponseSchema()
response_list_schema = StakeholderResponseSchema(many=True)

tag_create_schema = StakeholderTagCreateSchema()
tag_response_schema = StakeholderTagResponseSchema()
tag_list_schema = StakeholderTagResponseSchema(many=True)


class StakeholderController:

    @staticmethod
    def create():
        try:
            data = create_schema.load(request.get_json() or {})

            stakeholder = StakeholderService.create_stakeholder(
                data,
                g.auth_user,
                g.active_role,
            )

            return jsonify(
                response_schema.dump(stakeholder)
            ), 201

        except ValidationError as err:
            return jsonify(err.messages), 400

        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

        except IntegrityError as err:
            from app.database import db

            db.session.rollback()

            print("STAKEHOLDER CREATE INTEGRITY ERROR:")
            traceback.print_exc()

            return jsonify({
                "message": (
                    "Stakeholder could not be created because "
                    "the database rejected the record."
                ),
                "detail": str(getattr(err, "orig", err)),
            }), 409

        except SQLAlchemyError as err:
            from app.database import db

            db.session.rollback()

            print("STAKEHOLDER CREATE DATABASE ERROR:")
            traceback.print_exc()

            return jsonify({
                "message": (
                    "Stakeholder could not be saved because "
                    "of a database error."
                ),
                "detail": str(err),
            }), 500

        except Exception as err:
            from app.database import db

            db.session.rollback()

            print("STAKEHOLDER CREATE UNEXPECTED ERROR:")
            traceback.print_exc()

            return jsonify({
                "message": "Failed to create stakeholder",
                "detail": str(err),
            }), 500

    @staticmethod
    def get(stakeholder_id):
        stakeholder = StakeholderService.get_by_id(
            stakeholder_id,
            g.auth_user,
            g.active_role,
        )

        if not stakeholder:
            return jsonify({
                "message": "Stakeholder not found"
            }), 404

        return jsonify(
            response_schema.dump(stakeholder)
        ), 200

    @staticmethod
    def get_by_opportunity(opportunity_id):
        stakeholders = StakeholderService.get_by_opportunity(
            opportunity_id,
            g.auth_user,
            g.active_role,
        )

        return jsonify(
            response_list_schema.dump(stakeholders)
        ), 200

    @staticmethod
    def update(stakeholder_id):
        try:
            data = update_schema.load(
                request.get_json() or {}
            )

            stakeholder = StakeholderService.update_stakeholder(
                stakeholder_id,
                data,
                g.auth_user,
                g.active_role,
            )

            if not stakeholder:
                return jsonify({
                    "message": "Stakeholder not found"
                }), 404

            return jsonify(
                response_schema.dump(stakeholder)
            ), 200

        except ValidationError as err:
            return jsonify(err.messages), 400

        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

        except RuntimeError as err:
            return jsonify({"message": str(err)}), 409

        except Exception:
            return jsonify({
                "message": "Failed to update stakeholder"
            }), 500

    @staticmethod
    def delete(stakeholder_id):
        try:
            deleted = StakeholderService.delete_stakeholder(
                stakeholder_id,
                g.auth_user,
                g.active_role,
            )

            if not deleted:
                return jsonify({
                    "message": "Stakeholder not found"
                }), 404

            return jsonify({
                "message": "Stakeholder deleted"
            }), 200

        except AuthorizationDenied as err:
            return jsonify({"message": str(err)}), 403

        except Exception:
            return jsonify({
                "message": "Failed to delete stakeholder"
            }), 500

    # ------------------------------------------------------------------
    # B2 — Stakeholder Tags
    # ------------------------------------------------------------------

    @staticmethod
    def add_tag(stakeholder_id):
        try:
            data = tag_create_schema.load(
                request.get_json() or {}
            )

            stakeholder_tag = StakeholderService.add_tag(
                stakeholder_id,
                data["tag"],
                g.auth_user,
                g.active_role,
            )

            if not stakeholder_tag:
                return jsonify({
                    "message": "Stakeholder not found"
                }), 404

            return jsonify(
                tag_response_schema.dump(stakeholder_tag)
            ), 201

        except ValidationError as err:
            return jsonify(err.messages), 400

        except AuthorizationDenied as err:
            return jsonify({
                "message": str(err)
            }), 403

        except ValueError as err:
            return jsonify({
                "message": str(err)
            }), 409

        except IntegrityError as err:
            from app.database import db

            db.session.rollback()

            return jsonify({
                "message": (
                    "Stakeholder tag could not be created "
                    "because the database rejected the record."
                ),
                "detail": str(getattr(err, "orig", err)),
            }), 409

        except SQLAlchemyError as err:
            from app.database import db

            db.session.rollback()

            return jsonify({
                "message": (
                    "Stakeholder tag could not be saved "
                    "because of a database error."
                ),
                "detail": str(err),
            }), 500

        except Exception as err:
            from app.database import db

            db.session.rollback()

            print("STAKEHOLDER TAG CREATE UNEXPECTED ERROR:")
            traceback.print_exc()

            return jsonify({
                "message": "Failed to add stakeholder tag",
                "detail": str(err),
            }), 500

    @staticmethod
    def get_tags(stakeholder_id):
        try:
            tags = StakeholderService.get_tags(
                stakeholder_id,
                g.auth_user,
                g.active_role,
            )

            if tags is None:
                return jsonify({
                    "message": "Stakeholder not found"
                }), 404

            return jsonify(
                tag_list_schema.dump(tags)
            ), 200

        except AuthorizationDenied as err:
            return jsonify({
                "message": str(err)
            }), 403

        except Exception as err:
            return jsonify({
                "message": "Failed to get stakeholder tags",
                "detail": str(err),
            }), 500

    @staticmethod
    def remove_tag(stakeholder_tag_id):
        try:
            deleted = StakeholderService.remove_tag(
                stakeholder_tag_id,
                g.auth_user,
                g.active_role,
            )

            if not deleted:
                return jsonify({
                    "message": "Stakeholder tag not found"
                }), 404

            return jsonify({
                "message": "Stakeholder tag removed"
            }), 200

        except AuthorizationDenied as err:
            return jsonify({
                "message": str(err)
            }), 403

        except Exception as err:
            from app.database import db

            db.session.rollback()

            return jsonify({
                "message": "Failed to remove stakeholder tag",
                "detail": str(err),
            }), 500

    @staticmethod
    def get_decision_maker(opportunity_id):
        try:
            stakeholder_tag = StakeholderService.get_decision_maker(
                opportunity_id,
                g.auth_user,
                g.active_role,
            )

            if stakeholder_tag is None:
                return jsonify({
                    "message": "Decision Maker not found"
                }), 404

            return jsonify(
                tag_response_schema.dump(stakeholder_tag)
            ), 200

        except AuthorizationDenied as err:
            return jsonify({
                "message": str(err)
            }), 403

        except Exception as err:
            return jsonify({
                "message": "Failed to get decision maker",
                "detail": str(err),
            }), 500