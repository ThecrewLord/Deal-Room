from flask import Blueprint, request, jsonify, g, send_file

from app.auth.authorization import business_access_required
from app.services.phase2_service import Phase2Service
from app.services.poc_report_service import POCReportService

poc_bp = Blueprint("poc_compat", __name__, url_prefix="/api/poc")


def _payload(data):
    return dict(data or {})


def _poc(p):
    return {
        "poc_id": p.poc_id, "opportunity_id": p.opportunity_id, "poc_name": p.poc_name,
        "target_date": p.target_date.isoformat() if p.target_date else None,
        "result_view_link": p.result_view_link,
        "status": p.status, "outcome": p.outcome, "outcome_notes": p.outcome_notes,
        "requested_by": p.requested_by, "submitted_by": p.submitted_by,
        "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
        "row_version": p.row_version,
    }


@poc_bp.post("/request")
@business_access_required
def request_poc():
    data = _payload(request.get_json() or {})
    opportunity_id = data.pop("opportunity_id", None)
    if opportunity_id is None:
        return jsonify({"message": "opportunity_id is required"}), 400
    try:
        p = Phase2Service.request_poc(int(opportunity_id), data, g.auth_user, g.active_role)
        return jsonify(_poc(p)), 201
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 409


@poc_bp.get("/eligible-opportunities")
@business_access_required
def eligible_opportunities():
    rows = Phase2Service.eligible_poc_opportunities(g.auth_user, g.active_role)
    return jsonify([{"opportunity_id": o.opportunity_id, "opportunity_name": o.opportunity_name, "account_id": o.account_id} for o in rows])


@poc_bp.get("/<int:poc_id>/download")
@business_access_required
def download_poc(poc_id):
    try:
        buffer = POCReportService.generate_poc_pdf(poc_id, g.auth_user, g.active_role)
        if not buffer:
            return jsonify({"message": "POC not found"}), 404
        return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"POC-{poc_id}.pdf")
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403


@poc_bp.get("/<int:poc_id>")
@business_access_required
def get_poc(poc_id):
    p = Phase2Service.get_poc(poc_id, g.auth_user, g.active_role)
    return (jsonify({"message": "POC not found"}), 404) if not p else (jsonify(_poc(p)), 200)


@poc_bp.get("/opportunity/<int:opportunity_id>")
@business_access_required
def get_pocs_by_opportunity(opportunity_id):
    return jsonify([_poc(p) for p in Phase2Service.get_pocs_by_opportunity(opportunity_id, g.auth_user, g.active_role)])


@poc_bp.post("/<int:poc_id>/complete")
@business_access_required
def complete_poc(poc_id):
    try:
        p = Phase2Service.complete_poc(poc_id, g.auth_user, g.active_role)
        return (jsonify({"message": "POC not found"}), 404) if not p else jsonify(_poc(p))
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 409
