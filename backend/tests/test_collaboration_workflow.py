import pytest
from app import create_app
from app.database import db
from app.auth.password import hash_password
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.account.account import Account
from app.models.system.tag import Tag
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.stage_master import StageMaster
from app.models.account.oem_partner import OEMPartner
from app.models.phase2 import OEMOpportunity, DeliveryProject, DeliveryProjectMember
from app.services.account_service import AccountService
from app.services.stakeholder_service import StakeholderService
from app.services.oem_service import OEMService
from app.services.phase2_service import Phase2Service
from app.constants.roles import LEADERSHIP, SALES_EXECUTIVE, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST

@pytest.fixture()
def app(tmp_path):
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":f"sqlite:///{tmp_path/'p2.db'}","JWT_SECRET_KEY":"p2"})
    with app.app_context():
        db.drop_all(); db.create_all()
        for name in ["Economic Buyer","Technical Champion","End User","Blocker","Decision Maker"]:
            db.session.add(Tag(name=name,is_active=True))
        for order,name in enumerate(("Lead","Qualified","RFX","POC","Negotiations","Delivery"),1):
            db.session.add(StageMaster(stage_name=name,display_order=order,requires_poc=name=="POC",is_closed=False,is_won=False))
        ids={}
        for role in [LEADERSHIP,SALES_EXECUTIVE,SOLUTION_ENGINEER,DELIVERY_MANAGER,DEVOPS_ENGINEER,DATA_ANALYST]:
            u=User(full_name=role,email=role.lower().replace(" ","_")+"@test.local",password_hash=hash_password("Password123!"),status="APPROVED",active=True)
            u.roles.append(UserRole(role=role)); db.session.add(u)
        db.session.flush()
        for u in User.query.all(): ids[u.roles[0].role]=u.user_id
        account=Account(account_name="Acme  Corp",is_active=True); db.session.add(account); db.session.flush()
        app.config.update(P2_USERS=ids,P2_ACCOUNT=account.account_id)
        db.session.commit()
    return app

def U(app,role):
    return User.query.get(app.config["P2_USERS"][role])

def opp(app):
    from app.services.opportunity_service import OpportunityService
    with app.app_context():
        u=U(app,SALES_EXECUTIVE)
        return OpportunityService.create_opportunity({"account_id":app.config["P2_ACCOUNT"],"opportunity_name":"P2 Test","estimated_value":100,"description":"d","pain_points":"p"},u,SALES_EXECUTIVE).opportunity_id

def test_account_names_are_canonical_and_unique(app):
    with app.app_context():
        u=U(app,SALES_EXECUTIVE)
        with pytest.raises(ValueError): AccountService.create({"account_name":" acme   corp "},u,SALES_EXECUTIVE)
        b=AccountService.create({"account_name":"Banned Co"},u,SALES_EXECUTIVE)
        b.status="Banned"; b.is_active=False; db.session.commit()
        from app.services.opportunity_service import OpportunityService
        with pytest.raises(ValueError,match="this account is banned"):
            OpportunityService.create_opportunity({"account_id":b.account_id,"opportunity_name":"bad","estimated_value":1},u,SALES_EXECUTIVE)

def test_only_one_decision_maker_is_allowed(app):
    oid=opp(app)
    with app.app_context():
        u=U(app,SALES_EXECUTIVE)
        a=StakeholderService.create_stakeholder({"opportunity_id":oid,"name":"A","tags":["Decision Maker"]},u,SALES_EXECUTIVE)
        with pytest.raises(ValueError):
            StakeholderService.create_stakeholder({"opportunity_id":oid,"name":"B","tags":["Decision Maker"]},u,SALES_EXECUTIVE)

def test_oem_contacts_are_redacted_for_employees(app):
    with app.app_context():
        lead=U(app,LEADERSHIP); se=U(app,SOLUTION_ENGINEER)
        o=OEMService.create({"account_id":app.config["P2_ACCOUNT"],"partner_name":"OEM","product_name":"P","contact_person":"Secret","email":"secret@test","phone":"123"},lead,LEADERSHIP)
        assert "contact_person" not in __import__("app.controllers.oem_controller",fromlist=["serialize"]).serialize(o,se,SOLUTION_ENGINEER)

def test_poc_team_is_limited_to_two_members(app):
    oid=opp(app)
    with app.app_context():
        o=Opportunity.query.get(oid); o.lifecycle_stage="POC"; o.review_status="Approved"; o.sales_owner_id=U(app,SALES_EXECUTIVE).user_id
        se=U(app,SOLUTION_ENGINEER); dm=U(app,DELIVERY_MANAGER)
        db.session.add(OpportunityTeam(opportunity_id=oid,user_id=se.user_id,role=SOLUTION_ENGINEER)); db.session.commit()
        p=Phase2Service.request_poc(oid,{"objective":"o","success_metrics":"s","exit_criteria":"e","input_drive_link":"https://drive.google.com/x","target_date":__import__("datetime").date.today(),"failure_condition":"f"},se,SOLUTION_ENGINEER)
        with pytest.raises(ValueError,match="at most two"):
            Phase2Service.assign_poc_team(p.poc_id,[U(app,DEVOPS_ENGINEER).user_id,U(app,DATA_ANALYST).user_id,1],dm,DELIVERY_MANAGER)

def test_delivery_project_is_a_separate_aggregate(app):
    with app.app_context():
        se=U(app,SOLUTION_ENGINEER); dm=U(app,DELIVERY_MANAGER); stage=StageMaster.query.filter_by(stage_name="Delivery").first()
        o=Opportunity(account_id=app.config["P2_ACCOUNT"],created_by=se.user_id,stage_id=stage.stage_id,opportunity_name="Won",estimated_value=500,lifecycle_stage="Delivery",outcome="Closed Won",operational_status="Closed",review_status="Approved",row_version=1,status="Closed",is_active=False)
        db.session.add(o); db.session.flush()
        p=Phase2Service.create_delivery_project(o,se,SOLUTION_ENGINEER)
        assert p.opportunity_id==o.opportunity_id and p.account_id==o.account_id and DeliveryProject.query.filter_by(opportunity_id=o.opportunity_id).count()==1
