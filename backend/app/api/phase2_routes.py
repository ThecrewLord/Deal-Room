from flask import Blueprint, request, jsonify, g, send_file

from app.auth.authorization import phase2_auth_required, AuthorizationService
from app.services.phase2_service import Phase2Service
from app.services.lifecycle_transition_service import TransitionConflict, TransitionInvalid
from app.services.poc_report_service import POCReportService
from app.models.system.tag import Tag

phase2_bp = Blueprint("phase2", __name__, url_prefix="/api/v2")


def err(fn):
    try:
        return fn()
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403
    except TransitionConflict as exc:
        return jsonify({"message": str(exc)}), 409
    except TransitionInvalid as exc:
        return jsonify({"message": str(exc)}), 422
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 409


def _poc(p):
    return {
        "poc_id": p.poc_id,
        "opportunity_id": p.opportunity_id,
        "poc_name": p.poc_name,
        "target_date": p.target_date.isoformat() if p.target_date else None,
        "result_view_link": p.result_view_link,
        "status": p.status,
        "outcome": p.outcome,
        "outcome_notes": p.outcome_notes,
        "requested_by": p.requested_by,
        "submitted_by": p.submitted_by,
        "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
        "row_version": p.row_version,
        "permission_disclaimer": "Ensure the assigned team has the required Google Drive access. The application does not verify Drive permissions.",
        "team": [{"user_id": m.user_id, "role": m.role} for m in p.team_members],
    }


def _neg(n):
    return {
        "negotiation_context_id": n.negotiation_context_id,
        "nda_suggested": n.nda_suggested,
        "nda_link": n.nda_link,
        "msa_link": n.msa_link,
        "sow_link": n.sow_link,
        "notes": n.notes,
        "row_version": n.row_version,
    }


def _project(p):
    return {
        "delivery_project_id": p.delivery_project_id,
        "opportunity_id": p.opportunity_id,
        "account_id": p.account_id,
        "manager_id": p.manager_id,
        "status": p.status,
        "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        "row_version": p.row_version,
        "members": [
            {
                "delivery_project_member_id": m.delivery_project_member_id,
                "user_id": m.user_id,
                "is_done": m.is_done,
                "is_suggested": m.is_suggested,
                "completed_at": m.completed_at.isoformat() if m.completed_at else None,
            }
            for m in p.members
        ],
    }


def _fu(f):
    return {
        "follow_up_id": f.follow_up_id,
        "owner_id": f.owner_id,
        "description": f.description,
        "due_date": f.due_date.isoformat(),
        "status": f.status,
        "completed_at": f.completed_at.isoformat() if f.completed_at else None,
        "created_by": f.created_by,
    }


@phase2_bp.get("/tags")
@phase2_auth_required
def tags():
    return jsonify([{"tag_id": t.tag_id, "name": t.name} for t in Tag.query.filter_by(is_active=True).order_by(Tag.name).all()])


@phase2_bp.get("/oem/<int:oid>")
@phase2_auth_required
def oem_assoc(oid):
    rows = Phase2Service.oem_associations(oid, g.auth_user, g.active_role)
    return jsonify([{"opportunity_oem_id": x.opportunity_oem_id, "oem_partner_id": x.oem_partner_id, "partner_name": x.oem.partner_name, "product_name": x.oem.product_name} for x in rows])


@phase2_bp.put("/opportunity/<int:oid>/oems")
@phase2_auth_required
def set_oems(oid):
    return err(lambda: jsonify([{"oem_partner_id": x.oem_partner_id, "partner_name": x.oem.partner_name} for x in Phase2Service.set_oems(oid, (request.get_json() or {}).get("oem_ids", []), g.auth_user, g.active_role)]))


@phase2_bp.get("/opportunity/<int:oid>/rfx")
@phase2_auth_required
def get_rfx(oid):
    c = Phase2Service.get_rfx(oid, g.auth_user, g.active_role)
    if c is None:
        return jsonify({"message": "RFX context not found"}), 404
    return jsonify({
        "drive_link": c.drive_link,
        "row_version": c.row_version,
        "permission_disclaimer": "The application stores the supplied Drive reference but does not verify Drive permissions, folder existence, or Google account access.",
    })


@phase2_bp.put("/opportunity/<int:oid>/rfx")
@phase2_auth_required
def put_rfx(oid):
    def action():
        c = Phase2Service.update_rfx(oid, request.get_json() or {}, g.auth_user, g.active_role)
        if c is None:
            return jsonify({"message": "Opportunity not found"}), 404
        return jsonify({
            "drive_link": c.drive_link,
            "row_version": c.row_version,
            "permission_disclaimer": "The application stores the supplied Drive reference but does not verify Drive permissions, folder existence, or Google account access.",
        })
    return err(action)


@phase2_bp.post("/opportunity/<int:oid>/pocs")
@phase2_auth_required
def request_poc(oid):
    def action():
        p = Phase2Service.request_poc(oid, request.get_json() or {}, g.auth_user, g.active_role)
        if not p:
            return jsonify({"message": "Opportunity not found"}), 404
        return jsonify(_poc(p)), 201
    return err(action)

@phase2_bp.post("/opportunity/<int:oid>/pocs/request-new")
@phase2_auth_required
def request_new_poc(oid):
    def action():
        p = Phase2Service.request_new_poc(
            oid, request.get_json() or {}, g.auth_user, g.active_role
        )
        if not p:
            return jsonify({"message": "Opportunity not found"}), 404
        return jsonify(_poc(p)), 201
    return err(action)


@phase2_bp.get("/poc/eligible-opportunities")
@phase2_auth_required
def eligible_poc_opportunities():
    rows = Phase2Service.eligible_poc_opportunities(g.auth_user, g.active_role)
    return jsonify([{"opportunity_id": o.opportunity_id, "opportunity_name": o.opportunity_name, "account_id": o.account_id} for o in rows])


@phase2_bp.get("/pocs/<int:poc_id>")
@phase2_auth_required
def get_poc2(poc_id):
    p = Phase2Service.get_poc(poc_id, g.auth_user, g.active_role)
    if not p:
        return jsonify({"message": "POC not found"}), 404
    return jsonify(_poc(p))


@phase2_bp.get("/opportunity/<int:oid>/pocs")
@phase2_auth_required
def get_pocs_by_opportunity(oid):
    return jsonify([_poc(p) for p in Phase2Service.get_pocs_by_opportunity(oid, g.auth_user, g.active_role)])


@phase2_bp.get("/pocs/<int:poc_id>/download")
@phase2_auth_required
def download_poc(poc_id):
    try:
        buffer = POCReportService.generate_poc_pdf(poc_id, g.auth_user, g.active_role)
        if not buffer:
            return jsonify({"message": "POC not found"}), 404
        return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"POC-{poc_id}.pdf")
    except PermissionError as exc:
        return jsonify({"message": str(exc)}), 403


@phase2_bp.post("/pocs/<int:poc_id>/team")
@phase2_auth_required
def assign_poc_team(poc_id):
    def action():
        rows = Phase2Service.assign_poc_team(poc_id, (request.get_json() or {}).get("member_ids", []), g.auth_user, g.active_role)
        if rows is None:
            return jsonify({"message": "POC not found"}), 404
        return jsonify([{"user_id": m.user_id, "role": m.role} for m in rows])
    return err(action)


@phase2_bp.post("/pocs/<int:poc_id>/submit")
@phase2_auth_required
def submit_poc(poc_id):
    def action():
        p = Phase2Service.submit_poc(poc_id, request.get_json() or {}, g.auth_user, g.active_role)
        if not p:
            return jsonify({"message": "POC not found"}), 404
        return jsonify(_poc(p))
    return err(action)


@phase2_bp.post("/pocs/<int:poc_id>/complete")
@phase2_auth_required
def complete_poc(poc_id):
    def action():
        p = Phase2Service.complete_poc(poc_id, g.auth_user, g.active_role)
        if not p:
            return jsonify({"message": "POC not found"}), 404
        return jsonify(_poc(p))
    return err(action)


@phase2_bp.get("/opportunity/<int:oid>/negotiations")
@phase2_auth_required
def get_neg(oid):
    o = Phase2Service._opp(oid)
    if not o or not AuthorizationService.can_view_opportunity(g.auth_user, g.active_role, o):
        return jsonify({"message": "Not found"}), 404
    n = o.negotiation_context
    return jsonify(_neg(n) if n else {})


@phase2_bp.put("/opportunity/<int:oid>/negotiations")
@phase2_auth_required
def put_neg(oid):
    return err(lambda: jsonify(_neg(Phase2Service.update_negotiation(oid, request.get_json() or {}, g.auth_user, g.active_role))))


@phase2_bp.get("/opportunity/<int:oid>/delivery-project")
@phase2_auth_required
def get_delivery(oid):
    p = Phase2Service.get_delivery(oid, g.auth_user, g.active_role)
    if not p:
        return jsonify({"message": "Delivery Project not found"}), 404
    return jsonify(_project(p))


@phase2_bp.put("/delivery-project/<int:pid>/members")
@phase2_auth_required
def set_members(pid):
    return err(lambda: jsonify(_project(Phase2Service.assign_delivery_members(pid, (request.get_json() or {}).get("member_ids", []), g.auth_user, g.active_role))))


@phase2_bp.post("/delivery-project/<int:pid>/complete")
@phase2_auth_required
def complete_project(pid):
    return err(lambda: jsonify(_project(Phase2Service.complete_project(pid, g.auth_user, g.active_role))))


@phase2_bp.post("/delivery-project-members/<int:mid>/done")
@phase2_auth_required
def complete_member(mid):
    return err(lambda: jsonify({"member_id": Phase2Service.complete_member(mid, g.auth_user, g.active_role).delivery_project_member_id, "status": "Done"}))


@phase2_bp.get("/opportunity/<int:oid>/activities")
@phase2_auth_required
def activities(oid):
    return jsonify([{"activity_id": a.activity_id, "activity_type": a.activity_type, "summary": a.summary, "actor_id": a.actor_id, "created_at": a.created_at.isoformat()} for a in Phase2Service.activities(oid, g.auth_user, g.active_role)])


@phase2_bp.post("/opportunity/<int:oid>/activities")
@phase2_auth_required
def add_activity(oid):
    return err(lambda: (jsonify({"activity_id": (a := Phase2Service.add_activity(oid, request.get_json() or {}, g.auth_user, g.active_role)).activity_id, "summary": a.summary}), 201))


@phase2_bp.get("/opportunity/<int:oid>/follow-ups")
@phase2_auth_required
def followups(oid):
    return jsonify([_fu(x) for x in Phase2Service.followups(oid, g.auth_user, g.active_role)])


@phase2_bp.post("/opportunity/<int:oid>/follow-ups")
@phase2_auth_required
def add_followup(oid):
    return err(lambda: (jsonify(_fu(Phase2Service.add_followup(oid, request.get_json() or {}, g.auth_user, g.active_role))), 201))


@phase2_bp.post("/follow-ups/<int:fid>/complete")
@phase2_auth_required
def complete_followup(fid):
    return err(lambda: jsonify(_fu(Phase2Service.complete_followup(fid, g.auth_user, g.active_role))))
