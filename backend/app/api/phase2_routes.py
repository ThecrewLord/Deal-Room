from flask import Blueprint, request, jsonify, g
from app.auth.authorization import phase2_auth_required
from app.services.phase2_service import Phase2Service
from app.models.account.oem_partner import OEMPartner
from app.models.system.tag import Tag
from app.models.phase2 import POCTeamMember, DeliveryProjectMember, DeliveryProject
from app.models.opportunity.poc_tracker import POCTracker

phase2_bp=Blueprint("phase2",__name__,url_prefix="/api/v2")

def err(fn):
    try: return fn()
    except PermissionError as e: return jsonify({"message":str(e)}),403
    except ValueError as e: return jsonify({"message":str(e)}),409

@phase2_bp.get("/tags")
@phase2_auth_required
def tags(): return jsonify([{"tag_id":t.tag_id,"name":t.name} for t in Tag.query.filter_by(is_active=True).order_by(Tag.name).all()])

@phase2_bp.get("/oem/<int:oid>")
@phase2_auth_required
def oem_assoc(oid):
    rows=Phase2Service.oem_associations(oid,g.auth_user,g.active_role)
    return jsonify([{"opportunity_oem_id":x.opportunity_oem_id,"oem_partner_id":x.oem_partner_id,"partner_name":x.oem.partner_name,"product_name":x.oem.product_name} for x in rows])

@phase2_bp.put("/opportunity/<int:oid>/oems")
@phase2_auth_required
def set_oems(oid): return err(lambda: jsonify([{"oem_partner_id":x.oem_partner_id,"partner_name":x.oem.partner_name} for x in Phase2Service.set_oems(oid,(request.get_json() or {}).get("oem_ids",[]),g.auth_user,g.active_role)]))

@phase2_bp.get("/opportunity/<int:oid>/rfx")
@phase2_auth_required
def get_rfx(oid):
    c=Phase2Service.get_rfx(oid,g.auth_user,g.active_role)
    return jsonify({"drive_link":c.drive_link if c else None,"permission_disclaimer":"Ensure the assigned team has the required Google Drive access. The application does not verify Drive permissions."})

@phase2_bp.put("/opportunity/<int:oid>/rfx")
@phase2_auth_required
def put_rfx(oid): return err(lambda: jsonify({"drive_link":Phase2Service.update_rfx(oid,request.get_json() or {},g.auth_user,g.active_role).drive_link}))

@phase2_bp.post("/opportunity/<int:oid>/pocs")
@phase2_auth_required
def request_poc(oid): return err(lambda: (jsonify(_poc(Phase2Service.request_poc(oid,request.get_json() or {},g.auth_user,g.active_role))),201))

def _poc(p):
    return {"poc_id":p.poc_id,"opportunity_id":p.opportunity_id,"poc_name":p.poc_name,"objective":p.objective,"success_metrics":p.success_metric,"exit_criteria":p.exit_criteria,"target_date":p.target_date.isoformat() if p.target_date else None,"failure_condition":p.failure_condition,"input_drive_link":p.input_drive_link,"result_view_link":p.result_view_link,"status":p.status,"outcome":p.outcome,"outcome_notes":p.outcome_notes,"requested_by":p.requested_by,"submitted_by":p.submitted_by,"submitted_at":p.submitted_at.isoformat() if p.submitted_at else None,"team":[{"user_id":m.user_id,"role":m.role} for m in p.team_members]}

@phase2_bp.get("/pocs/<int:poc_id>")
@phase2_auth_required
def get_poc2(poc_id):
    p=POCTracker.query.get(poc_id)
    if not p: return jsonify({"message":"POC not found"}),404
    from app.auth.authorization import AuthorizationService
    if not AuthorizationService.can_view_poc(g.auth_user,g.active_role,p): return jsonify({"message":"Forbidden"}),403
    return jsonify(_poc(p))

@phase2_bp.post("/pocs/<int:poc_id>/team")
@phase2_auth_required
def assign_poc_team(poc_id): return err(lambda: jsonify([{"user_id":m.user_id,"role":m.role} for m in Phase2Service.assign_poc_team(poc_id,(request.get_json() or {}).get("member_ids",[]),g.auth_user,g.active_role)]))

@phase2_bp.post("/pocs/<int:poc_id>/submit")
@phase2_auth_required
def submit_poc(poc_id): return err(lambda: jsonify(_poc(Phase2Service.submit_poc(poc_id,request.get_json() or {},g.auth_user,g.active_role))))

@phase2_bp.get("/opportunity/<int:oid>/negotiations")
@phase2_auth_required
def get_neg(oid):
    from app.auth.authorization import AuthorizationService
    o=Phase2Service._opp(oid)
    if not o or not AuthorizationService.can_view_opportunity(g.auth_user,g.active_role,o): return jsonify({"message":"Not found"}),404
    n=o.negotiation_context
    return jsonify({"nda_suggested":n.nda_suggested,"nda_link":n.nda_link,"msa_link":n.msa_link,"sow_link":n.sow_link,"notes":n.notes} if n else {})

@phase2_bp.put("/opportunity/<int:oid>/negotiations")
@phase2_auth_required
def put_neg(oid): return err(lambda: jsonify(_neg(Phase2Service.update_negotiation(oid,request.get_json() or {},g.auth_user,g.active_role))))
def _neg(n): return {"negotiation_context_id":n.negotiation_context_id,"nda_suggested":n.nda_suggested,"nda_link":n.nda_link,"msa_link":n.msa_link,"sow_link":n.sow_link,"notes":n.notes,"row_version":n.row_version}

@phase2_bp.get("/opportunity/<int:oid>/delivery-project")
@phase2_auth_required
def get_delivery(oid):
    p=Phase2Service.get_delivery(oid,g.auth_user,g.active_role)
    if not p: return jsonify({"message":"Delivery Project not found"}),404
    return jsonify(_project(p))

def _project(p): return {"delivery_project_id":p.delivery_project_id,"opportunity_id":p.opportunity_id,"account_id":p.account_id,"manager_id":p.manager_id,"status":p.status,"completed_at":p.completed_at.isoformat() if p.completed_at else None,"row_version":p.row_version,"members":[{"delivery_project_member_id":m.delivery_project_member_id,"user_id":m.user_id,"is_done":m.is_done,"completed_at":m.completed_at.isoformat() if m.completed_at else None} for m in p.members]}

@phase2_bp.put("/delivery-project/<int:pid>/members")
@phase2_auth_required
def set_members(pid): return err(lambda: jsonify(_project(Phase2Service.assign_delivery_members(pid,(request.get_json() or {}).get("member_ids",[]),g.auth_user,g.active_role))))

@phase2_bp.post("/delivery-project/<int:pid>/complete")
@phase2_auth_required
def complete_project(pid): return err(lambda: jsonify(_project(Phase2Service.complete_project(pid,g.auth_user,g.active_role))))

@phase2_bp.post("/delivery-project-members/<int:mid>/done")
@phase2_auth_required
def complete_member(mid): return err(lambda: jsonify({"member_id":Phase2Service.complete_member(mid,g.auth_user,g.active_role).delivery_project_member_id,"status":"Done"}))

@phase2_bp.get("/opportunity/<int:oid>/activities")
@phase2_auth_required
def activities(oid): return jsonify([{"activity_id":a.activity_id,"activity_type":a.activity_type,"summary":a.summary,"actor_id":a.actor_id,"created_at":a.created_at.isoformat()} for a in Phase2Service.activities(oid,g.auth_user,g.active_role)])

@phase2_bp.post("/opportunity/<int:oid>/activities")
@phase2_auth_required
def add_activity(oid): return err(lambda: (jsonify({"activity_id":(a:=Phase2Service.add_activity(oid,request.get_json() or {},g.auth_user,g.active_role)).activity_id,"summary":a.summary}),201))

@phase2_bp.get("/opportunity/<int:oid>/follow-ups")
@phase2_auth_required
def followups(oid): return jsonify([_fu(x) for x in Phase2Service.followups(oid,g.auth_user,g.active_role)])
def _fu(f): return {"follow_up_id":f.follow_up_id,"owner_id":f.owner_id,"description":f.description,"due_date":f.due_date.isoformat(),"status":f.status,"completed_at":f.completed_at.isoformat() if f.completed_at else None,"created_by":f.created_by}

@phase2_bp.post("/opportunity/<int:oid>/follow-ups")
@phase2_auth_required
def add_followup(oid): return err(lambda: (jsonify(_fu(Phase2Service.add_followup(oid,request.get_json() or {},g.auth_user,g.active_role))),201))

@phase2_bp.post("/follow-ups/<int:fid>/complete")
@phase2_auth_required
def complete_followup(fid): return err(lambda: jsonify(_fu(Phase2Service.complete_followup(fid,g.auth_user,g.active_role))))
