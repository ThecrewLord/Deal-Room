from flask import Blueprint, jsonify

from app.services.dashboard_service import (
    get_weighted_forecast,
    get_total_opportunities,
    get_total_pipeline_value,
    get_conversion_rate,
    get_stalled_deals,
    get_active_pocs,
    get_partner_contribution
)


dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


@dashboard_bp.route(
    "/dashboard/metrics",
    methods=["GET"]
)
def dashboard_metrics():

    return jsonify({

        "weighted_forecast":
            get_weighted_forecast(),

        "total_opportunities":
            get_total_opportunities(),

        "total_pipeline_value":
            get_total_pipeline_value(),

        "conversion_rate":
            get_conversion_rate(),

        "stalled_deals":
            get_stalled_deals(),

        "active_pocs":
            get_active_pocs(),

        "partner_contribution":
            get_partner_contribution()

    })