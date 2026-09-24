from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.roles import SALES_EXECUTIVE
from app.database import db
from app.models.opportunity.stakeholder import Stakeholder
from app.models.system.tag import Tag
from app.services.activity_service import ActivityService
from sqlalchemy.exc import IntegrityError
class StakeholderService:
    @staticmethod
    def _set_tags(stakeholder, names):
        names=list(dict.fromkeys(names or []))
        tags={t.name:t for t in Tag.query.filter(Tag.name.in_(names),Tag.is_active.is_(True)).all()}
        if len(tags)!=len(names): raise ValueError("One or more stakeholder tags are invalid.")
        stakeholder.tags=[tags[n] for n in names]
        stakeholder.is_decision_maker=("Decision Maker" in names)
    @staticmethod
    def create_stakeholder(data,user,active_role):
        opp=Stakeholder.query.session.get(__import__("app.models.opportunity.opportunity",fromlist=["Opportunity"]).Opportunity,data["opportunity_id"])
        if not opp: return None
        if not AuthorizationService.can_mutate_related(user,active_role,opp,"stakeholder","create"):
            raise AuthorizationDenied("You are not authorized to create stakeholders for this opportunity.")
        st=Stakeholder(name=data["name"],job_title=data.get("job_title"),email=data.get("email"),phone=data.get("phone"),company=data.get("company"),notes=data.get("notes"),opportunity_id=opp.opportunity_id)
        try:
            db.session.add(st); db.session.flush(); StakeholderService._set_tags(st,data.get("tags",[]))
            ActivityService.log("Stakeholder",st.stakeholder_id,"STAKEHOLDER_CREATED",f"Stakeholder '{st.name}' created.",user.user_id,commit=False,active_role=active_role)
            db.session.commit(); return st
        except IntegrityError:
            db.session.rollback(); raise ValueError("Only one Decision Maker may exist per Opportunity.")
    @staticmethod
    def get_by_id(stakeholder_id,user,active_role):
        st=Stakeholder.query.get(stakeholder_id); return st if st and AuthorizationService.can_view_stakeholder(user,active_role,st) else None
    @staticmethod
    def get_by_opportunity(opportunity_id,user,active_role):
        from app.models.opportunity.opportunity import Opportunity
        opp=Opportunity.query.get(opportunity_id)
        return Stakeholder.query.filter_by(opportunity_id=opportunity_id).all() if opp and AuthorizationService.can_view_opportunity(user,active_role,opp) else []
    @staticmethod
    def update_stakeholder(stakeholder_id,data,user,active_role):
        st=Stakeholder.query.get(stakeholder_id)
        if not st: return None
        if not AuthorizationService.can_mutate_related(user,active_role,st.opportunity,"stakeholder","update"): raise AuthorizationDenied("You are not authorized to update this stakeholder.")
        if st.opportunity.operational_status=="Closed": raise AuthorizationDenied("Closed opportunities are locked.")
        if active_role==SALES_EXECUTIVE and any(k in data for k in {"name","job_title","email","phone","company"}):
            raise AuthorizationDenied("Sales Executive cannot edit stakeholder identity fields.")
        for k in ("name","job_title","email","phone","company","notes"):
            if k in data: setattr(st,k,data[k])
        if "tags" in data: StakeholderService._set_tags(st,data["tags"])
        db.session.commit(); return st
    @staticmethod
    def delete_stakeholder(stakeholder_id,user,active_role):
        st=Stakeholder.query.get(stakeholder_id)
        if not st: return False
        if not AuthorizationService.can_mutate_related(user,active_role,st.opportunity,"stakeholder","delete"): raise AuthorizationDenied("You are not authorized to delete this stakeholder.")
        db.session.delete(st); db.session.commit(); return True
