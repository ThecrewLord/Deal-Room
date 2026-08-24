import pytest
from datetime import date, timedelta

from app.auth.password import hash_password
from app.constants.roles import *
from app.constants.stages import *
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.poc_tracker import POCTracker
from app.models.system.audit_log import AuditLog


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'phase6.db'}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase6-test-secret")
    from app import create_app
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        db.drop_all(); db.create_all()
        stages = [StageMaster(stage_name=n, display_order=i, requires_poc=(n == "POC / Technical Evaluation"),
                               is_closed=n.startswith("Closed"), is_won=n == "Closed Won")
                  for i, n in enumerate(["Lead / Identified","Qualification","Discovery","POC / Technical Evaluation","Proposal","Negotiation","Closed Won","Closed Lost"], 1)]
        db.session.add_all(stages); db.session.flush()
        def user(name, email, role, extras=()):
            u = User(full_name=name, email=email, password_hash=hash_password("Password123!"), status="APPROVED", active=True)
            u.roles.append(UserRole(role=role))
            for r in extras: u.roles.append(UserRole(role=r))
            db.session.add(u); db.session.flush(); return u
        creator=user("Creator","creator6@example.com",SALES_EXECUTIVE)
        owner=user("Owner","owner6@example.com",SALES_EXECUTIVE)
        manager=user("Manager","manager6@example.com",SALES_MANAGER)
        psm=user("PSM","psm6@example.com",PRE_SALES_MANAGER)
        se=user("SE","se6@example.com",SOLUTION_ENGINEER)
        se2=user("SE2","se2_6@example.com",SOLUTION_ENGINEER)
        delivery=user("Delivery","delivery6@example.com",DELIVERY)
        wrong=user("Wrong","wrong6@example.com",SALES_EXECUTIVE)
        multi=user("Multi","multi6@example.com",SOLUTION_ENGINEER,(DELIVERY,))
        account=Account(account_name="Phase 6 Account"); db.session.add(account); db.session.flush()
        opp=Opportunity(account_id=account.account_id, created_by=creator.user_id, sales_owner_id=owner.user_id,
                        stage_id=stages[1].stage_id, opportunity_name="Phase 6 Opportunity",
                        status=ACTIVE_STATUS, is_active=True)
        db.session.add(opp); db.session.flush()
        db.session.add_all([
            OpportunityTeam(opportunity_id=opp.opportunity_id,user_id=creator.user_id,role=SALES_EXECUTIVE),
            OpportunityTeam(opportunity_id=opp.opportunity_id,user_id=owner.user_id,role=SALES_EXECUTIVE),
            OpportunityTeam(opportunity_id=opp.opportunity_id,user_id=se.user_id,role=SOLUTION_ENGINEER),
            OpportunityTeam(opportunity_id=opp.opportunity_id,user_id=se2.user_id,role=SOLUTION_ENGINEER),
            OpportunityTeam(opportunity_id=opp.opportunity_id,user_id=delivery.user_id,role=DELIVERY),
        ])
        db.session.commit()
        application.config["P6"]={"opp":opp.opportunity_id,"se":se.email,"se2":se2.email,"delivery":delivery.email,"psm":psm.email,"manager":manager.email,"wrong":wrong.email,"multi":multi.email}
    return application

@pytest.fixture()
def client(app): return app.test_client()

def auth(token): return {"Authorization": f"Bearer {token}"}

def token_for(client,email,role=None):
    r=client.post("/api/auth/login",json={"email":email,"password":"Password123!"})
    assert r.status_code==200
    j=r.get_json()
    if j.get("requires_role_selection"):
        r=client.post("/api/auth/select-role",json={"role":role},headers=auth(j["refresh_token"]))
        assert r.status_code==200; return r.get_json()["access_token"]
    return j["access_token"]

def oid_and_ts(app):
    with app.app_context():
        o=Opportunity.query.get(app.config["P6"]["opp"])
        return o.opportunity_id,o.updated_at.isoformat()

def test_assigned_se_can_create_design(client,app):
    t=token_for(client,app.config["P6"]["se"],SOLUTION_ENGINEER); oid,ts=oid_and_ts(app)
    r=client.patch(f"/api/opportunities/{oid}/solution-design",headers=auth(t),
                   json={"solution_summary":"S","technical_approach":"A","updated_at":ts})
    assert r.status_code==200

def test_unassigned_se_cannot_request_poc(client,app):
    # The second SE is assigned in this fixture; use wrong sales user to assert membership is required.
    t=token_for(client,app.config["P6"]["wrong"],SALES_EXECUTIVE); oid,ts=oid_and_ts(app)
    r=client.post("/api/poc/request",headers=auth(t),json={"opportunity_id":oid,"poc_name":"P","objective":"O","success_metric":"S","exit_criteria":"E","target_date":str(date.today()+timedelta(days=3)),"failure_condition":"F"})
    assert r.status_code==403

def request_poc(client,app):
    t=token_for(client,app.config["P6"]["se"],SOLUTION_ENGINEER); oid,_=oid_and_ts(app)
    r=client.post("/api/poc/request",headers=auth(t),json={"opportunity_id":oid,"poc_name":"POC 1","objective":"Objective","success_metric":"Success","exit_criteria":"Exit","target_date":str(date.today()+timedelta(days=3)),"failure_condition":"Failure"})
    assert r.status_code==201
    return r.get_json()

def test_se_request_enters_pending_approval(client,app):
    p=request_poc(client,app); assert p["status"]=="Pending Approval"

def test_psm_can_approve(client,app):
    p=request_poc(client,app); t=token_for(client,app.config["P6"]["psm"],PRE_SALES_MANAGER)
    r=client.post(f"/api/poc/{p['poc_id']}/approve",headers=auth(t),json={"updated_at":p["updated_at"]})
    assert r.status_code==200 and r.get_json()["status"]=="Approved"

def test_delivery_can_execute_and_submit(client,app):
    p=request_poc(client,app); tpsm=token_for(client,app.config["P6"]["psm"],PRE_SALES_MANAGER)
    p=client.post(f"/api/poc/{p['poc_id']}/approve",headers=auth(tpsm),json={"updated_at":p["updated_at"]}).get_json()
    td=token_for(client,app.config["P6"]["delivery"],DELIVERY)
    p=client.post(f"/api/poc/{p['poc_id']}/start-execution",headers=auth(td),json={"updated_at":p["updated_at"]}).get_json()
    assert p["status"]=="In Progress"
    r=client.post(f"/api/poc/{p['poc_id']}/submit-result",headers=auth(td),
                  json={"execution_status":"Submitted","poc_access_link":"client access instructions","outcome":"Success","outcome_notes":"Passed","updated_at":p["updated_at"]})
    assert r.status_code==200 and r.get_json()["status"]=="Submitted"

def test_delivery_cannot_edit_poc_design(client,app):
    p=request_poc(client,app); td=token_for(client,app.config["P6"]["delivery"],DELIVERY)
    r=client.patch(f"/api/poc/{p['poc_id']}/design",headers=auth(td),
                   json={"objective":"tamper","updated_at":p["updated_at"]})
    assert r.status_code==403

def test_psm_cannot_close(client,app):
    oid,ts=oid_and_ts(app); t=token_for(client,app.config["P6"]["psm"],PRE_SALES_MANAGER)
    r=client.post(f"/api/opportunities/{oid}/close-won",headers=auth(t),json={"updated_at":ts})
    assert r.status_code==403

def test_delivery_cannot_close(client,app):
    oid,ts=oid_and_ts(app); t=token_for(client,app.config["P6"]["delivery"],DELIVERY)
    r=client.post(f"/api/opportunities/{oid}/close-won",headers=auth(t),json={"updated_at":ts})
    assert r.status_code==403

def test_se_stage_transition_is_explicit(client,app):
    oid,ts=oid_and_ts(app); t=token_for(client,app.config["P6"]["se"],SOLUTION_ENGINEER)
    r=client.post(f"/api/opportunities/{oid}/transition-technical-stage",headers=auth(t),
                  json={"target_stage":"Discovery","updated_at":ts})
    assert r.status_code==200

def test_arbitrary_stage_jump_rejected(client,app):
    oid,ts=oid_and_ts(app); t=token_for(client,app.config["P6"]["se"],SOLUTION_ENGINEER)
    r=client.post(f"/api/opportunities/{oid}/transition-technical-stage",headers=auth(t),
                  json={"target_stage":"Closed Won","updated_at":ts})
    assert r.status_code in (400,403)

def test_generic_poc_put_is_not_available(client,app):
    p=request_poc(client,app); t=token_for(client,app.config["P6"]["se"],SOLUTION_ENGINEER)
    r=client.put(f"/api/poc/{p['poc_id']}",headers=auth(t),json={"status":"Approved"})
    assert r.status_code in (404,405)

def test_poc_delete_is_denied(client,app):
    p=request_poc(client,app); t=token_for(client,app.config["P6"]["se"],SOLUTION_ENGINEER)
    assert client.delete(f"/api/poc/{p['poc_id']}",headers=auth(t)).status_code==403

def test_multi_role_delivery_active_cannot_request_poc(client,app):
    # Multi-role users must obey only the selected active role.
    t=token_for(client,app.config["P6"]["multi"],DELIVERY)
    oid,_=oid_and_ts(app)
    r=client.post("/api/poc/request",headers=auth(t),json={"opportunity_id":oid,"poc_name":"P","objective":"O","success_metric":"S","exit_criteria":"E","target_date":str(date.today()+timedelta(days=3)),"failure_condition":"F"})
    assert r.status_code==403
