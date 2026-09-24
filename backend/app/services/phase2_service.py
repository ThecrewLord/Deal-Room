from datetime import date, datetime
from urllib.parse import urlparse
from sqlalchemy import update
from app.database import db
from app.auth.authorization import AuthorizationService, AuthorizationDenied
from app.constants.roles import SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST
from app.constants.poc_outcome import POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.account.oem_partner import OEMPartner
from app.models.phase2 import OEMOpportunity, RFXContext, NegotiationContext, POCTeamMember, DeliveryProject, DeliveryProjectMember, Activity, FollowUp
from app.models.auth.user import User
from app.services.activity_service import ActivityService
from app.services.notification_service import NotificationService
from app.services.poc_history_service import POCHistoryService
from app.services.lifecycle_transition_service import TransitionConflict, TransitionInvalid

class Phase2Service:
    @staticmethod
    def _opp(oid):
        return db.session.get(Opportunity, oid)

    @staticmethod
    def _poc(poc_id):
        return db.session.get(POCTracker, poc_id)

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
    def _validate_drive_link(value):
        if value is None:
            raise TransitionInvalid("Google Drive folder link is required.")
        link = str(value).strip()
        parsed = urlparse(link)
        if not link or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise TransitionInvalid("drive_link must be a valid URL.")
        if parsed.netloc.lower() not in {"drive.google.com", "www.drive.google.com"}:
            raise TransitionInvalid("drive_link must reference Google Drive.")
        return link

    @staticmethod
    def update_rfx(oid,data,user,role):
        # Lock the opportunity so create-vs-update remains one authoritative
        # RFX context even under concurrent requests.
        o = Opportunity.query.filter_by(opportunity_id=oid).with_for_update().first()
        if not o:
            return None
        if not AuthorizationService.can_manage_rfx(user,role,o):
            raise AuthorizationDenied("You are not authorized to manage RFX context.")

        allowed = {"drive_link", "drive_folder_link", "row_version"}
        unexpected = set(data or {}) - allowed
        if unexpected:
            raise TransitionInvalid("Only RFX-owned fields may be updated.")

        raw_link = data.get("drive_folder_link", data.get("drive_link"))
        link = Phase2Service._validate_drive_link(raw_link)
        ctx = RFXContext.query.filter_by(opportunity_id=oid).with_for_update().first()

        expected = data.get("row_version")
        if ctx is None:
            # Creation is the first version of the RFX aggregate. There is no
            # prior RFX row to compare against, so the client receives version 1.
            if expected not in (None, 0, 1):
                raise TransitionConflict("RFX context version is stale. Refresh before retrying.")
            ctx = RFXContext(
                opportunity_id=oid,
                drive_link=link,
                row_version=1,
                created_by=user.user_id,
                updated_by=user.user_id,
            )
            db.session.add(ctx)
            db.session.flush()
            old_link = None
            action = "RFX_CONTEXT_CREATED"
        else:
            try:
                expected_version = int(expected)
            except (TypeError, ValueError):
                raise TransitionInvalid("row_version is required and must be an integer for RFX updates.")
            if expected_version != ctx.row_version:
                raise TransitionConflict("RFX context version is stale. Refresh before retrying.")
            old_link = ctx.drive_link
            result = db.session.execute(
                update(RFXContext)
                .where(
                    RFXContext.rfx_context_id == ctx.rfx_context_id,
                    RFXContext.row_version == expected_version,
                )
                .values(
                    drive_link=link,
                    updated_by=user.user_id,
                    updated_at=datetime.utcnow(),
                    row_version=RFXContext.row_version + 1,
                )
            )
            if result.rowcount != 1:
                raise TransitionConflict("RFX context version is stale. Refresh before retrying.")
            db.session.expire(ctx)
            db.session.refresh(ctx)
            action = "RFX_CONTEXT_UPDATED"

        ActivityService.log(
            "Opportunity", oid, action,
            f"RFX Google Drive context changed from '{old_link}' to '{link}'.",
            user.user_id, commit=False, active_role=role,
        )
        db.session.commit()
        return ctx

    @staticmethod
    def get_poc(poc_id,user,role):
        p=Phase2Service._poc(poc_id)
        if not p or not AuthorizationService.can_view_poc(user,role,p):
            return None
        return p

    @staticmethod
    def get_pocs_by_opportunity(oid,user,role):
        o=Phase2Service._opp(oid)
        if not o or not AuthorizationService.can_view_opportunity(user,role,o):
            return []
        return POCTracker.query.filter_by(opportunity_id=oid).order_by(POCTracker.created_at.asc()).all()

    @staticmethod
    def eligible_poc_opportunities(user,role):
        if role != SOLUTION_ENGINEER:
            return []
        rows=(Opportunity.query
              .join(OpportunityTeam, OpportunityTeam.opportunity_id == Opportunity.opportunity_id)
              .filter(
                  OpportunityTeam.user_id == user.user_id,
                  OpportunityTeam.role == SOLUTION_ENGINEER,
                  Opportunity.lifecycle_stage == "POC",
                  Opportunity.operational_status == "Active",
              )
              .order_by(Opportunity.updated_at.desc())
              .all())
        eligible=[]
        for opportunity in rows:
            active_poc=POCTracker.query.filter(
                POCTracker.opportunity_id == opportunity.opportunity_id,
                POCTracker.status.in_({"Draft", "In Progress", "Submitted"}),
            ).first()
            if not active_poc:
                eligible.append(opportunity)
        return eligible

    @staticmethod
    def request_new_poc(oid, data, user, role):
        """Request another POC cycle without involving the Delivery Manager.

        The latest completed/submitted POC remains immutable as business data.
        A new POCTracker cycle is created for the same existing DE/DA team,
        while the latest POC row_version acts as the optimistic-concurrency
        token for the repeat request.
        """
        o = Opportunity.query.filter_by(opportunity_id=oid).with_for_update().first()
        if not o:
            return None

        if not AuthorizationService.can_request_new_poc(user, role, o):
            raise AuthorizationDenied(
                "Only the assigned Solution Engineer can request a new POC."
            )

        if o.lifecycle_stage != "POC" or o.operational_status == "Closed" or o.outcome != "Open":
            raise ValueError("Opportunity must be open at POC stage.")

        allowed = {"reason", "row_version"}
        unexpected = set(data or {}) - allowed
        if unexpected:
            raise TransitionInvalid("Only reason and row_version may be supplied.")

        reason = str((data or {}).get("reason") or "").strip()
        if not reason:
            raise ValueError("reason is required.")

        try:
            expected_version = int((data or {}).get("row_version"))
        except (TypeError, ValueError):
            raise TransitionInvalid("row_version is required and must be an integer.")

        latest = (
            POCTracker.query
            .filter_by(opportunity_id=oid)
            .order_by(POCTracker.created_at.desc(), POCTracker.poc_id.desc())
            .with_for_update()
            .first()
        )
        if not latest or latest.status not in {POC_STATUS_SUBMITTED, POC_STATUS_COMPLETED}:
            raise ValueError("A completed or submitted POC is required before requesting a new POC.")

        if expected_version != latest.row_version:
            raise TransitionConflict("POC version is stale. Refresh before retrying.")

        existing_members = list(
            POCTeamMember.query
            .filter_by(poc_id=latest.poc_id)
            .order_by(POCTeamMember.poc_team_member_id.asc())
            .all()
        )
        if not existing_members:
            raise ValueError("An existing POC team is required before requesting a new POC.")

        try:
            # Carry the POC aggregate version forward to the new cycle. The
            # prior submitted POC remains untouched, while a retry using its
            # stale version cannot match the newly-created latest cycle.
            new_poc = POCTracker(
                poc_name=f"POC Cycle {POCTracker.query.filter_by(opportunity_id=oid).count() + 1}",
                opportunity_id=oid,
                target_date=latest.target_date,
                requested_by=user.user_id,
                status="Draft",
                remarks=None,
                row_version=latest.row_version + 1,
            )
            db.session.add(new_poc)
            db.session.flush()

            for member in existing_members:
                db.session.add(
                    POCTeamMember(
                        poc_id=new_poc.poc_id,
                        user_id=member.user_id,
                        role=member.role,
                        assigned_by=member.assigned_by,
                        assigned_at=member.assigned_at,
                    )
                )

            POCHistoryService.record_poc_history(
                o.opportunity_id, user, "NEW_POC_REQUESTED", reason
            )
            ActivityService.log(
                "POC",
                new_poc.poc_id,
                "NEW_POC_REQUESTED",
                f"New POC requested for '{o.opportunity_name}'.",
                user.user_id,
                commit=False,
                active_role=role,
            )

            for member in existing_members:
                NotificationService.queue(
                    member.user_id,
                    "NEW_POC_REQUESTED",
                    "POC",
                    new_poc.poc_id,
                    f"New POC requested for opportunity '{o.opportunity_name}'. Reason: {reason}",
                )

            db.session.commit()
            return new_poc
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def request_poc(oid,data,user,role):
        o=Phase2Service._opp(oid)
        if not o: return None
        if role != SOLUTION_ENGINEER or not AuthorizationService.is_assigned_role(user,o,SOLUTION_ENGINEER): raise AuthorizationDenied("Only an assigned Solution Engineer can request a POC.")
        if o.lifecycle_stage!="POC" or o.operational_status=="Closed": raise ValueError("Opportunity must be open at POC stage.")
        allowed={"poc_name","target_date","remarks"}
        unexpected=set(data or {})-allowed
        if unexpected:
            raise TransitionInvalid("Only POC workflow fields may be supplied.")
        if not data.get("target_date"):
            raise ValueError("Missing required POC information: target_date")
        target_date=data["target_date"]
        if isinstance(target_date,str):
            try:
                target_date=date.fromisoformat(target_date)
            except ValueError as exc:
                raise ValueError("target_date must be a valid ISO date (YYYY-MM-DD).") from exc
        if target_date < date.today():
            raise ValueError("target_date cannot be in the past.")
        p=POCTracker(
            poc_name=data.get("poc_name") or f"POC Cycle {POCTracker.query.filter_by(opportunity_id=oid).count()+1}",
            opportunity_id=oid,
            target_date=target_date,
            requested_by=user.user_id,
            status="Draft",
            remarks=data.get("remarks"),
        )
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
        p=Phase2Service._poc(poc_id)
        if not p: return None
        if not AuthorizationService.can_request_poc_team_assignment(user,role,p): raise AuthorizationDenied("Only Delivery Manager or Leadership can assign the POC team.")
        if p.status not in {"Draft", "In Progress"}: raise ValueError("POC team can only be assigned while the POC is active.")
        ids=list(dict.fromkeys(int(x) for x in (member_ids or [])))
        if len(ids)>2: raise ValueError("A POC may have at most two team members.")
        users={u.user_id:u for u in User.query.filter(User.user_id.in_(ids)).all()}
        if len(users)!=len(ids): raise ValueError("One or more POC team members do not exist.")
        for uid in ids:
            u=users[uid]
            if not (u.has_role(DEVOPS_ENGINEER) or u.has_role(DATA_ANALYST)): raise ValueError("POC team members may only be DevOps Engineer or Data Analyst.")
        p.row_version += 1
        POCTeamMember.query.filter_by(poc_id=poc_id).delete(synchronize_session=False)
        for uid in ids:
            u=users[uid]; member_role=DEVOPS_ENGINEER if u.has_role(DEVOPS_ENGINEER) and not u.has_role(DATA_ANALYST) else DATA_ANALYST
            db.session.add(POCTeamMember(poc_id=poc_id,user_id=uid,role=member_role,assigned_by=user.user_id))
        ActivityService.log("POC",poc_id,"POC_ASSIGNED",f"POC team assigned: {ids}.",user.user_id,commit=False,active_role=role)
        db.session.commit(); return POCTeamMember.query.filter_by(poc_id=poc_id).all()

    @staticmethod
    def submit_poc(poc_id, data, user, role):
        data = data or {}
        # Lock the authoritative POC row where the database supports row locks.
        # The conditional UPDATE below remains the source of truth for the
        # optimistic-concurrency boundary, including SQLite test environments.
        p = POCTracker.query.filter_by(poc_id=poc_id).with_for_update().first()
        if not p:
            return None

        if not AuthorizationService.can_submit_poc_result(user, role, p):
            raise AuthorizationDenied("Only an assigned POC team member can submit the result.")

        allowed = {"result_view_link", "row_version"}
        unexpected = set(data or {}) - allowed
        if unexpected:
            raise TransitionInvalid("Only result_view_link and row_version may be supplied.")

        if p.status not in {"Draft", "In Progress"} or p.submitted_at is not None:
            raise TransitionInvalid("Only an active, unsubmitted POC can be submitted.")

        link = data.get("result_view_link")
        if not isinstance(link, str) or not link.strip():
            raise TransitionInvalid("result_view_link is required and must be a non-empty URL.")
        link = link.strip()
        parsed = urlparse(link)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise TransitionInvalid("result_view_link must be a valid URL.")

        try:
            expected_version = int(data.get("row_version"))
        except (TypeError, ValueError):
            raise TransitionInvalid("row_version is required and must be an integer.")

        if expected_version != p.row_version:
            raise TransitionConflict("POC version is stale. Refresh before retrying.")

        # Resolve the recipient before mutating anything so a malformed
        # assignment cannot leave a partially prepared transaction.
        se_recipients = [
            tm.user_id
            for tm in p.opportunity.team_members
            if tm.role == SOLUTION_ENGINEER and tm.user_id is not None
        ]
        if not se_recipients:
            raise TransitionInvalid("No assigned Solution Engineer exists for this opportunity.")

        submitted_at = datetime.utcnow()
        result = db.session.execute(
            update(POCTracker)
            .where(
                POCTracker.poc_id == poc_id,
                POCTracker.row_version == expected_version,
                POCTracker.status.in_(["Draft", "In Progress"]),
                POCTracker.submitted_at.is_(None),
            )
            .values(
                start_date=p.start_date or date.today(),
                status=POC_STATUS_SUBMITTED,
                result_view_link=link,
                submitted_by=user.user_id,
                submitted_at=submitted_at,
                end_date=date.today(),
                row_version=POCTracker.row_version + 1,
            )
        )
        if result.rowcount != 1:
            raise TransitionConflict("POC version is stale or the POC was already submitted.")

        db.session.expire(p)
        db.session.refresh(p)

        # Group 5 already owns immutable POC history; preserve that existing
        # integration rather than introducing another history mechanism here.
        POCHistoryService.record_poc_history(p.opportunity_id, user, "POC_SUBMITTED")
        ActivityService.log(
            "POC", poc_id, "POC_SUBMITTED", "POC result submitted.",
            user.user_id, commit=False, active_role=role,
        )

        # Business mutation, history and audit commit first. Notifications are
        # deliberately published only after that commit so a rollback cannot
        # produce a false POC_SUBMITTED notification.
        db.session.commit()

        try:
            for recipient_id in dict.fromkeys(se_recipients):
                NotificationService.queue(
                    recipient_id,
                    "POC_SUBMITTED",
                    "POC",
                    poc_id,
                    f"POC '{p.poc_name}' result is ready for review.",
                )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return p

    @staticmethod
    def complete_poc(poc_id,user,role):
        p=Phase2Service._poc(poc_id)
        if not p:
            return None
        if not AuthorizationService.can_complete_poc(user,role,p):
            raise AuthorizationDenied("Only the assigned Solution Engineer can complete a submitted POC.")
        p.status=POC_STATUS_COMPLETED
        p.row_version += 1
        ActivityService.log(
            "POC", p.poc_id, "POC_COMPLETED",
            f"POC '{p.poc_name}' marked completed after Solution Engineer review.",
            user.user_id, commit=False, active_role=role,
        )
        db.session.commit()
        return p

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
                db.session.add(DeliveryProjectMember(delivery_project_id=p.delivery_project_id,user_id=tm.user_id,assigned_by=manager.user_id,is_suggested=True))
        ActivityService.log("DeliveryProject",p.delivery_project_id,"DELIVERY_PROJECT_CREATED","Delivery Project created from Closed Won.",user.user_id,commit=False,active_role=role)
        NotificationService.queue(manager.user_id,"DELIVERY_PROJECT_CREATED","Opportunity",o.opportunity_id,f"Delivery Project created for '{o.opportunity_name}'.")
        return p

    @staticmethod
    def assign_delivery_members(project_id,member_ids,user,role):
        p=db.session.get(DeliveryProject, project_id)
        if not p: return None
        if not AuthorizationService.can_manage_delivery_project(user,role,p): raise AuthorizationDenied("Only Delivery Manager or Leadership can manage project membership.")
        ids=list(dict.fromkeys(int(x) for x in (member_ids or [])))
        users={u.user_id:u for u in User.query.filter(User.user_id.in_(ids)).all()}
        if len(users)!=len(ids): raise ValueError("One or more members do not exist.")
        for uid in ids:
            if not (users[uid].has_role(DEVOPS_ENGINEER) or users[uid].has_role(DATA_ANALYST)): raise ValueError("Only valid delivery team roles may be assigned.")
        p.members.clear()
        for uid in ids: db.session.add(DeliveryProjectMember(delivery_project_id=p.delivery_project_id,user_id=uid,assigned_by=user.user_id,is_suggested=False))
        p.row_version+=1
        ActivityService.log("DeliveryProject",p.delivery_project_id,"DELIVERY_PROJECT_MEMBERS_CHANGED","Delivery Project membership changed.",user.user_id,commit=False,active_role=role)
        db.session.commit(); return p

    @staticmethod
    def complete_project(project_id,user,role):
        p=db.session.get(DeliveryProject, project_id)
        if not p: return None
        if not AuthorizationService.can_manage_delivery_project(user,role,p): raise AuthorizationDenied("Only Delivery Manager or Leadership can complete the project.")
        p.status="Done"; p.completed_at=datetime.utcnow(); p.row_version+=1
        db.session.commit(); return p

    @staticmethod
    def complete_member(member_id,user,role):
        m=db.session.get(DeliveryProjectMember, member_id)
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
        owner=db.session.get(User, int(data.get("owner_id") or user.user_id))
        if not owner: raise ValueError("Follow-up owner does not exist.")
        f=FollowUp(opportunity_id=oid,owner_id=owner.user_id,description=str(data.get("description") or "").strip(),due_date=data.get("due_date"),created_by=user.user_id,status="Open")
        if not f.description or not f.due_date: raise ValueError("Follow-up description and due date are required.")
        db.session.add(f); db.session.flush(); ActivityService.log("FollowUp",f.follow_up_id,"FOLLOW_UP_CREATED","Follow-up created.",user.user_id,commit=False,active_role=role); db.session.commit(); return f

    @staticmethod
    def complete_followup(fid,user,role):
        f=db.session.get(FollowUp, fid)
        if not f: return None
        if not AuthorizationService.can_manage_followup(user,role,f): raise AuthorizationDenied("You are not authorized to complete this follow-up.")
        f.status="Completed"; f.completed_at=datetime.utcnow(); db.session.commit(); return f
