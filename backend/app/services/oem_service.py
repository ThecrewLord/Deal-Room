from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.database import db
from app.models.account.oem_partner import OEMPartner
from app.models.account.account import Account
from app.services.activity_service import ActivityService
class OEMService:
    @staticmethod
    def get_all(user, active_role): return OEMPartner.query.order_by(OEMPartner.partner_name).all()
    @staticmethod
    def get_by_id(oem_id,user,active_role):
        o=OEMPartner.query.get(oem_id); return o if o and AuthorizationService.can_view_oem(user,active_role,o) else None
    @staticmethod
    def create(data,user,active_role):
        if not AuthorizationService.can_mutate_oem_master(user,active_role): raise AuthorizationDenied("Only Leadership can manage OEM master data.")
        if not data.get("partner_name") or not data.get("product_name"): raise ValueError("OEM name and product are required.")
        if data.get("account_id") and not Account.query.get(data["account_id"]): raise ValueError("Account does not exist.")
        o=OEMPartner(account_id=data.get("account_id") or Account.query.first().account_id,partner_name=data["partner_name"].strip(),product_name=data["product_name"].strip(),contact_person=data.get("contact_person"),email=data.get("email"),phone=data.get("phone"),status=data.get("status","Active"),notes=data.get("notes"))
        db.session.add(o); db.session.flush(); ActivityService.log("OEM",o.oem_partner_id,"OEM_CREATED",f"OEM '{o.partner_name}' created.",user.user_id,commit=False,active_role=active_role); db.session.commit(); return o
    @staticmethod
    def update(oem_id,data,user,active_role):
        if not AuthorizationService.can_mutate_oem_master(user,active_role): raise AuthorizationDenied("Only Leadership can manage OEM master data.")
        o=OEMPartner.query.get(oem_id)
        if not o: return None
        for k in ("partner_name","product_name","contact_person","email","phone","status","notes","account_id"):
            if k in data: setattr(o,k,data[k])
        ActivityService.log("OEM",o.oem_partner_id,"OEM_UPDATED",f"OEM '{o.partner_name}' updated.",user.user_id,commit=False,active_role=active_role); db.session.commit(); return o
    @staticmethod
    def delete(oem_id,user,active_role):
        if not AuthorizationService.can_mutate_oem_master(user,active_role): raise AuthorizationDenied("Only Leadership can manage OEM master data.")
        o=OEMPartner.query.get(oem_id)
        if not o: return False
        if o.opportunity_associations: raise ValueError("OEM is referenced by opportunities and cannot be deleted.")
        db.session.delete(o); db.session.commit(); return True
