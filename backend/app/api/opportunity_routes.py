from flask import Blueprint

from app.controllers.opportunity_controller import (
    OpportunityController,
)

opportunity_bp = Blueprint(
    "opportunity",
    __name__,
    url_prefix="/api/opportunities",
)


opportunity_bp.route(
    "",
    methods=["POST"],
)(
    OpportunityController.create
)

opportunity_bp.route(
    "",
    methods=["GET"],
)(
    OpportunityController.get_all
)

opportunity_bp.route(
    "/<int:opportunity_id>",
    methods=["GET"],
)(
    OpportunityController.get
)

opportunity_bp.route(
    "/<int:opportunity_id>",
    methods=["PUT"],
)(
    OpportunityController.update
)

opportunity_bp.route(
    "/<int:opportunity_id>",
    methods=["DELETE"],
)(
    OpportunityController.delete
)