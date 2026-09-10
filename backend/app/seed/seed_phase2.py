from app.database import db
from app.models.account.account import Account
from app.models.account.oem_partner import OEMPartner
from app.models.system.tag import Tag
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.stakeholder import Stakeholder
from app.models.phase2 import OEMOpportunity, RFXContext, NegotiationContext, POCTeamMember, DeliveryProject, DeliveryProjectMember, Activity, FollowUp
from app.models.auth.user import User
from app.constants.roles import SALES_EXECUTIVE, LEADERSHIP, SOLUTION_ENGINEER, PRE_SALES_MANAGER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST

def _user(role):
    return User.query.filter(User.active.is_(True),User.status=="APPROVED",User.roles.any(role=role)).first()

def seed_phase2():
    tagmap={}
    for name in ["Economic Buyer","Technical Champion","End User","Blocker","Decision Maker"]:
        t=Tag.query.filter_by(name=name).first()
        if not t:
            t=Tag(name=name,is_active=True); db.session.add(t); db.session.flush()
        tagmap[name]=t
    base=Account.query.first()
    if not base: return
    for name,status in [("V2 Active Account","Active"),("V2 Archived Account","Archived"),("V2 Banned Account","Banned")]:
        c=" ".join(name.lower().split())
        if not Account.query.filter_by(canonical_name=c).first():
            db.session.add(Account(account_name=name,canonical_name=c,status=status,is_active=status=="Active",industry="Technology"))
    db.session.flush()
    o=Opportunity.query.filter_by(opportunity_name="V2 Demo Lead").first()
    if o and not o.stakeholders:
        db.session.add(Stakeholder(opportunity_id=o.opportunity_id,name="Alex Buyer",job_title="VP Technology",email="alex@example.com",company=o.account.account_name,is_decision_maker=True,tags=[tagmap["Decision Maker"],tagmap["Economic Buyer"]]))
    if not OEMPartner.query.filter_by(partner_name="V2 OEM Partner").first():
        db.session.add(OEMPartner(account_id=base.account_id,partner_name="V2 OEM Partner",product_name="V2 Platform",status="Active",contact_person="OEM Contact",email="oem@example.com",phone="+1-555-0100",notes="Leadership-only contact details."))
    db.session.flush()
    oem=OEMPartner.query.filter_by(partner_name="V2 OEM Partner").first()
    if o and not OEMOpportunity.query.filter_by(opportunity_id=o.opportunity_id,oem_partner_id=oem.oem_partner_id).first():
        db.session.add(OEMOpportunity(opportunity_id=o.opportunity_id,oem_partner_id=oem.oem_partner_id,created_by=o.created_by))
    # A deterministic closed-won path with two historical POC cycles and a Delivery Project.
    if not Opportunity.query.filter_by(opportunity_name="V2 Closed Won").first():
        se=_user(SOLUTION_ENGINEER) or _user(LEADERSHIP); dm=_user(DELIVERY_MANAGER) or _user(LEADERSHIP)
        dev=_user(DEVOPS_ENGINEER); analyst=_user(DATA_ANALYST)
        sm=StageMaster.query.filter_by(stage_name="Delivery").first()
        if se and dm and sm:
            cw=Opportunity(account_id=base.account_id,created_by=se.user_id,sales_owner_id=_user(SALES_EXECUTIVE).user_id if _user(SALES_EXECUTIVE) else None,stage_id=sm.stage_id,opportunity_name="V2 Closed Won",description="Deterministic Phase 2 closed-won example.",pain_points="Seed pain",estimated_value=500000,final_revenue=500000,probability=100,lifecycle_stage="Delivery",outcome="Closed Won",operational_status="Closed",review_status="Approved",row_version=1,status="Closed",is_active=False)
            db.session.add(cw); db.session.flush()
            db.session.add(OpportunityTeam(opportunity_id=cw.opportunity_id,user_id=se.user_id,role=SOLUTION_ENGINEER))
            p1=POCTracker(opportunity_id=cw.opportunity_id,poc_name="V2 POC Cycle 1",objective="Validate platform",success_metric="Meets target",exit_criteria="Target met",target_date=__import__("datetime").date.today(),failure_condition="Escalate",input_drive_link="https://drive.google.com/v2-seed-1",result_view_link="https://example.com/result-1",outcome="Success",outcome_notes="Passed",status="Completed",requested_by=se.user_id,submitted_by=dev.user_id if dev else se.user_id,submitted_at=__import__("datetime").datetime.utcnow())
            p2=POCTracker(opportunity_id=cw.opportunity_id,poc_name="V2 POC Cycle 2",objective="Regression proof",success_metric="Stable",exit_criteria="No critical defects",target_date=__import__("datetime").date.today(),failure_condition="Escalate",input_drive_link="https://drive.google.com/v2-seed-2",result_view_link="https://example.com/result-2",outcome="Success",outcome_notes="Passed",status="Completed",requested_by=se.user_id,submitted_by=analyst.user_id if analyst else se.user_id,submitted_at=__import__("datetime").datetime.utcnow())
            db.session.add_all([p1,p2]); db.session.flush()
            if dev: db.session.add(POCTeamMember(poc_id=p2.poc_id,user_id=dev.user_id,role=DEVOPS_ENGINEER,assigned_by=dm.user_id))
            if analyst: db.session.add(POCTeamMember(poc_id=p2.poc_id,user_id=analyst.user_id,role=DATA_ANALYST,assigned_by=dm.user_id))
            db.session.add(RFXContext(opportunity_id=cw.opportunity_id,drive_link="https://drive.google.com/v2-rfx",created_by=se.user_id,updated_by=se.user_id))
            db.session.add(NegotiationContext(opportunity_id=cw.opportunity_id,nda_suggested=True,notes="Optional contract context",created_by=se.user_id))
            dp=DeliveryProject(opportunity_id=cw.opportunity_id,account_id=base.account_id,manager_id=dm.user_id,status="Active",row_version=1)
            db.session.add(dp); db.session.flush()
            if dev: db.session.add(DeliveryProjectMember(delivery_project_id=dp.delivery_project_id,user_id=dev.user_id,assigned_by=dm.user_id))
            if analyst: db.session.add(DeliveryProjectMember(delivery_project_id=dp.delivery_project_id,user_id=analyst.user_id,assigned_by=dm.user_id))
            db.session.add(Activity(opportunity_id=cw.opportunity_id,activity_type="meeting",summary="Seed customer handoff meeting",actor_id=se.user_id))
            db.session.add(FollowUp(opportunity_id=cw.opportunity_id,owner_id=dm.user_id,description="Seed overdue handoff follow-up",due_date=__import__("datetime").date.today()-__import__("datetime").timedelta(days=1),status="Overdue",created_by=se.user_id))
    db.session.commit()
