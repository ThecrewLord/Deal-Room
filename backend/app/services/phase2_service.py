from datetime import date, datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.database import db
from app.auth.authorization import AuthorizationService, AuthorizationDenied
from app.constants.roles import LEADERSHIP, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST
from app.constants.poc_outcome import POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.account.oem_partner import OEMPartner
from app.models.phase2 import OEMOpportunity, RFXContext, NegotiationContext, POCTeamMember, DeliveryProject, DeliveryProjectMember, Activity, FollowUp
from app.models.auth.user import User
from app.models.system.tag import Tag
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService

class Phase2Service:
    @staticmethod
    def _opp(oid):
        return Opportunity.query.get(oid)

    @staticmethod
    def oem_associations(oid,user,role):
        o=Phase2Service._opp(oid)
        if not o or not AuthorizationService.can_view_opportunity(user,role,o): return []
        return OEMOpportunity.query.filter_by(opportunity_id=oid).all()

    @staticmethod
    def set_oems(oid,oem_ids,user,role):
        o=Phase2Service._opp(oid)
        if not o: return None
        if not AuthorizationService.can_manage_oem_association(user,role,o): raise AuthorizationDenied("You are not authorized to manage OEM associations.")
        ids=list(dict.fromkeys(int(x) for x in (oem_ids or [])))
        oems=OEMPartner.query.filter(OEMPartner.oem_partner_id.in_(ids)).all() if ids else []
        if len(oems)!=len(ids): raise ValueError("One or more OEMs do not exist.")
        existing=OEMOpportunity.query.filter_by(opportunity_id=oid).all()
        for x in existing: db.session.delete(x)
        db.session.flush()
        for x in oems: db.session.add(OEMOpportunity(opportunity_id=oid,oem_partner_id=x.oem_partner_id,created_by=user.user_id))
        ActivityService.log("Opportunity",oid,"OEM_ASSOCIATIONS_CHANGED",f"{len(ids)} OEM association(s) set.",user.user_id,commit=False,active_role=role)
        db.session.commit()
        return OEMOpportunity.query.filter_by(opportunity_id=oid).all()

    @staticmethod
    def get_rfx(oid,user,role):
        o=Phase2Service._opp(oid)
        return o.rfx_context if o and AuthorizationService.can_view_opportunity(user,role,o) else None

    @staticmethod
    def update_rfx(oid,data,user,role):
        o=Phase2Service._opp(oid)
        if not o: return None
        if not AuthorizationService.can_manage_rfx(user,role,o): raise AuthorizationDenied("You are not authorized to manage RFX context.")
        link=data.get("drive_link")
        if not link: raise ValueError("Google Drive link is required when entering POC.")
        if o.lifecycle_stage != "RFX": raise ValueError("RFX context can only be captured while the Opportunity is in RFX.")
        ctx=o.rfx_context
        if not ctx: ctx=RFXContext(opportunity_id=oid,created_by=user.user_id); db.session.add(ctx)
        ctx.drive_link=str(link).strip(); ctx.updated_by=user.user_id
        ActivityService.log("Opportunity",oid,"RFX_CONTEXT_UPDATED","RFX Google Drive context updated.",user.user_id,commit=False,active_role=role)
        db.session.commit(); return ctx

    @staticmethod
    def request_poc(oid,data,user,role):
        o=Phase2Service._opp(oid)
        if not o: return None
        if role != SOLUTION_ENGINEER or not AuthorizationService.is_assigned_role(user,o,SOLUTION_ENGINEER): raise AuthorizationDenied("Only an assigned Solution Engineer can request a POC.")
        if o.lifecycle_stage!="POC" or o.operational_status=="Closed": raise ValueError("Opportunity must be open at POC stage.")
        required=["objective","success_metrics","exit_criteria","input_drive_link","target_date","failure_condition"]
        missing=[x for x in required if not data.get(x)]
        if missing: raise ValueError("Missing required POC information: "+", ".join(missing))
        p=POCTracker(poc_name=data.get("poc_name") or f"POC Cycle {POCTracker.query.filter_by(opportunity_id=oid).count()+1}",opportunity_id=oid,objective=data["objective"],success_metric=data["success_metrics"],exit_criteria=data["exit_criteria"],target_date=data["target_date"],failure_condition=data["failure_condition"],input_drive_link=data["input_drive_link"],requested_by=user.user_id,status="Draft",remarks=data.get("remarks"))
        db.session.add(p); db.session.flush()
        ActivityService.log("POC",p.poc_id,"POC_REQUESTED",f"POC '{p.poc_name}' requested.",user.user_id,commit=False,active_role=role)
        dms=User.query.filter(User.active.is_(True),User.status=="APPROVED",User.roles.any(role=DELIVERY_MANAGER)).all()
        for dm in dms:
            NotificationService.queue(
                dm.user_id,
                "POC_REQUESTED",
                "POC",
                p.poc_id,
                f"POC '{p.poc_name}' has been requested and is ready for Delivery Manager assignment.",
            )
        db.session.commit(); return p

    @staticmethod
    def assign_poc_team(poc_id,member_ids,user,role):
        p=POCTracker.query.get(poc_id)
        if not p: return None
        if not AuthorizationService.can_request_poc_team_assignment(user,role,p): raise AuthorizationDenied("Only Delivery Manager or Leadership can assign the POC team.")
        ids=list(dict.fromkeys(int(x) for x in (member_ids or [])))
        if len(ids)>2: raise ValueError("A POC may have at most two team members.")
        users={u.user_id:u for u in User.query.filter(User.user_id.in_(ids)).all()}
        if len(users)!=len(ids): raise ValueError("One or more POC team members do not exist.")
        for uid in ids:
            u=users[uid]
            if not (u.has_role(DEVOPS_ENGINEER) or u.has_role(DATA_ANALYST)): raise ValueError("POC team members may only be DevOps Engineer or Data Analyst.")
        POCTeamMember.query.filter_by(poc_id=poc_id).delete(synchronize_session=False)
        for uid in ids:
            u=users[uid]; member_role=DEVOPS_ENGINEER if u.has_role(DEVOPS_ENGINEER) and not u.has_role(DATA_ANALYST) else DATA_ANALYST
            db.session.add(POCTeamMember(poc_id=poc_id,user_id=uid,role=member_role,assigned_by=user.user_id))
        ActivityService.log("POC",poc_id,"POC_ASSIGNED",f"POC team assigned: {ids}.",user.user_id,commit=False,active_role=role)
        db.session.commit(); return POCTeamMember.query.filter_by(poc_id=poc_id).all()

    @staticmethod
    def submit_poc(poc_id,data,user,role):
        p=POCTracker.query.get(poc_id)
        if not p: return None
        if not AuthorizationService.can_submit_poc_result(user,role,p): raise AuthorizationDenied("Only an assigned POC team member can submit the result.")
        if p.status not in {"Draft","In Progress"}: raise ValueError("Only an active POC can be submitted.")
        link=data.get("result_view_link")
        if not link: raise ValueError("Result/view link is required.")
        p.status=POC_STATUS_SUBMITTED; p.result_view_link=link; p.outcome=data.get("outcome"); p.outcome_notes=data.get("outcome_notes"); p.submitted_by=user.user_id; p.submitted_at=datetime.utcnow(); p.end_date=date.today()
        ActivityService.log("POC",poc_id,"POC_SUBMITTED","POC result submitted.",user.user_id,commit=False,active_role=role)
        for tm in p.opportunity.team_members:
            if tm.role==SOLUTION_ENGINEER: NotificationService.queue(tm.user_id,"POC_SUBMITTED","POC",poc_id,f"POC '{p.poc_name}' result is ready for review.")
        db.session.commit(); return p

    @staticmethod
    def update_negotiation(oid,data,user,role):
        o=Phase2Service._opp(oid)
        if not o: return None
        if not AuthorizationService.can_manage_negotiation(user,role,o): raise AuthorizationDenied("You are not authorized to manage Negotiations.")
        if o.lifecycle_stage!="Negotiations": raise ValueError("Negotiation context is only available at Negotiations stage.")
        n=o.negotiation_context
        if not n: n=NegotiationContext(opportunity_id=oid,created_by=user.user_id); db.session.add(n)
        for k in ("nda_suggested","nda_link","msa_link","sow_link","notes"):
            if k in data: setattr(n,k,data[k])
        n.row_version+=1; n.updated_by=user.user_id
        ActivityService.log("Opportunity",oid,"NEGOTIATION_CONTEXT_UPDATED","Negotiation context updated.",user.user_id,commit=False,active_role=role)
        db.session.commit(); return n

    @staticmethod
    def get_delivery(oid,user,role):
        p=DeliveryProject.query.filter_by(opportunity_id=oid).first()
        return p if p and AuthorizationService.can_view_opportunity(user,role,p.opportunity) else None

    @staticmethod
    def create_delivery_project(o,user,role):
        if o.outcome!="Closed Won": return None
        if o.delivery_project: return o.delivery_project
        manager=User.query.filter(User.active.is_(True),User.status=="APPROVED",User.roles.any(role=DELIVERY_MANAGER)).first()
        if not manager: raise ValueError("No Delivery Manager is available.")
        p=DeliveryProject(opportunity_id=o.opportunity_id,account_id=o.account_id,manager_id=manager.user_id,status="Active",row_version=1)
        db.session.add(p); db.session.flush()
        # Proposed POC team only; Delivery Manager controls final membership.
        latest=POCTracker.query.filter_by(opportunity_id=o.opportunity_id).order_by(POCTracker.created_at.desc()).first()
        if latest:
            for tm in latest.team_members:
                db.session.add(DeliveryProjectMember(delivery_project_id=p.delivery_project_id,user_id=tm.user_id,assigned_by=manager.user_id))
        ActivityService.log("DeliveryProject",p.delivery_project_id,"DELIVERY_PROJECT_CREATED","Delivery Project created from Closed Won.",user.user_id,commit=False,active_role=role)
        NotificationService.queue(manager.user_id,"DELIVERY_PROJECT_CREATED","Opportunity",o.opportunity_id,f"Delivery Project created for '{o.opportunity_name}'.")
        return p

    @staticmethod
    def assign_delivery_members(project_id,member_ids,user,role):
        p=DeliveryProject.query.get(project_id)
        if not p: return None
        if not AuthorizationService.can_manage_delivery_project(user,role,p): raise AuthorizationDenied("Only Delivery Manager or Leadership can manage project membership.")
        ids=list(dict.fromkeys(int(x) for x in (member_ids or [])))
        users={u.user_id:u for u in User.query.filter(User.user_id.in_(ids)).all()}
        if len(users)!=len(ids): raise ValueError("One or more members do not exist.")
        for uid in ids:
            if not (users[uid].has_role(DEVOPS_ENGINEER) or users[uid].has_role(DATA_ANALYST)): raise ValueError("Only valid delivery team roles may be assigned.")
        p.members.clear()
        for uid in ids: db.session.add(DeliveryProjectMember(delivery_project_id=p.delivery_project_id,user_id=uid,assigned_by=user.user_id))
        p.row_version+=1
        ActivityService.log("DeliveryProject",p.delivery_project_id,"DELIVERY_PROJECT_MEMBERS_CHANGED","Delivery Project membership changed.",user.user_id,commit=False,active_role=role)
        db.session.commit(); return p

    @staticmethod
    def complete_project(project_id,user,role):
        p=DeliveryProject.query.get(project_id)
        if not p: return None
        if not AuthorizationService.can_manage_delivery_project(user,role,p): raise AuthorizationDenied("Only Delivery Manager or Leadership can complete the project.")
        p.status="Done"; p.completed_at=datetime.utcnow(); p.row_version+=1
        db.session.commit(); return p

    @staticmethod
    def complete_member(member_id,user,role):
        m=DeliveryProjectMember.query.get(member_id)
        if not m: return None
        if not AuthorizationService.can_update_project_member_done(user,role,m): raise AuthorizationDenied("You can only mark your own project participation as Done.")
        m.is_done=True; m.completed_at=datetime.utcnow(); db.session.commit(); return m

    @staticmethod
    def activities(oid,user,role):
        o=Phase2Service._opp(oid)
        return Activity.query.filter_by(opportunity_id=oid).order_by(Activity.created_at.desc()).all() if o and AuthorizationService.can_view_opportunity(user,role,o) else []

    @staticmethod
    def add_activity(oid,data,user,role):
        o=Phase2Service._opp(oid)
        if not AuthorizationService.can_create_activity(user,role,o): raise AuthorizationDenied("You are not authorized to add activities.")
        a=Activity(opportunity_id=oid,activity_type=data.get("activity_type","note"),summary=str(data.get("summary") or "").strip(),actor_id=user.user_id)
        if not a.summary: raise ValueError("Activity summary is required.")
        db.session.add(a); db.session.flush()
        ActivityService.log("Activity",a.activity_id,"ACTIVITY_CREATED","Business activity recorded.",user.user_id,commit=False,active_role=role)
        db.session.commit(); return a

    @staticmethod
    def followups(oid,user,role):
        o=Phase2Service._opp(oid)
        if not o or not AuthorizationService.can_view_opportunity(user,role,o): return []
        rows=FollowUp.query.filter_by(opportunity_id=oid).order_by(FollowUp.due_date.asc()).all()
        for x in rows:
            if x.status=="Open" and x.due_date < date.today(): x.status="Overdue"
        db.session.commit()
        return rows

    @staticmethod
    def add_followup(oid,data,user,role):
        o=Phase2Service._opp(oid)
        if not AuthorizationService.can_manage_followup(user,role,None,o): raise AuthorizationDenied("You are not authorized to create follow-ups.")
        owner=User.query.get(int(data.get("owner_id") or user.user_id))
        if not owner: raise ValueError("Follow-up owner does not exist.")
        f=FollowUp(opportunity_id=oid,owner_id=owner.user_id,description=str(data.get("description") or "").strip(),due_date=data.get("due_date"),created_by=user.user_id,status="Open")
        if not f.description or not f.due_date: raise ValueError("Follow-up description and due date are required.")
        db.session.add(f); db.session.flush(); ActivityService.log("FollowUp",f.follow_up_id,"FOLLOW_UP_CREATED","Follow-up created.",user.user_id,commit=False,active_role=role); db.session.commit(); return f

    @staticmethod
    def complete_followup(fid,user,role):
        f=FollowUp.query.get(fid)
        if not f: return None
        if not AuthorizationService.can_manage_followup(user,role,f): raise AuthorizationDenied("You are not authorized to complete this follow-up.")
        f.status="Completed"; f.completed_at=datetime.utcnow(); db.session.commit(); return f
