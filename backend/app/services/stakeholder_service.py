from datetime import datetime
from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.constants.roles import SALES_EXECUTIVE
from app.database import db
from sqlalchemy import update
from app.services.lifecycle_transition_service import TransitionConflict
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.opportunity import Opportunity
from app.models.account.account import Account
from app.models.system.tag import Tag
from app.services.activity_service import ActivityService
from sqlalchemy.exc import IntegrityError
class StakeholderRoleConflict(ValueError):
    """Raised when a stakeholder role is already assigned in the opportunity."""


def _validate_phone(phone):
    if phone is None or phone == "":
        return

    if not isinstance(phone, str) or not phone.isdigit() or len(phone) != 10:
        raise ValueError("Phone number must contain exactly 10 digits.")


class StakeholderService:
    @staticmethod
    def _set_tags(stakeholder, names):
        names = list(dict.fromkeys(names or []))
        tags = {
            t.name: t
            for t in Tag.query.filter(
                Tag.name.in_(names),
                Tag.is_active.is_(True),
            ).all()
        }

        if len(tags) != len(names):
            raise ValueError("One or more stakeholder tags are invalid.")

        # Each supported stakeholder role may belong to only one
        # stakeholder within the SAME opportunity.
        #
        # A single stakeholder may still have multiple different roles.
        # Example:
        #   Rahul -> Economic Buyer + Decision Maker   (allowed)
        #
        # But:
        #   Rahul -> Economic Buyer
        #   Priya -> Economic Buyer                    (blocked)
        #
        # Exclude the stakeholder currently being edited so that retaining
        # an existing tag does not incorrectly trigger the duplicate check.
        if names:
            from app.models.opportunity.stakeholder import stakeholder_tag_links

            duplicate_rows = (
                db.session.query(Tag.name, Stakeholder.name)
                .join(
                    stakeholder_tag_links,
                    stakeholder_tag_links.c.tag_id == Tag.tag_id,
                )
                .join(
                    Stakeholder,
                    Stakeholder.stakeholder_id
                    == stakeholder_tag_links.c.stakeholder_id,
                )
                .filter(
                    Stakeholder.opportunity_id == stakeholder.opportunity_id,
                    Tag.name.in_(names),
                    Stakeholder.stakeholder_id != stakeholder.stakeholder_id,
                )
                .all()
            )

            if duplicate_rows:
                role, existing_name = duplicate_rows[0]
                raise StakeholderRoleConflict(
                    f"{role} is already assigned to {existing_name} "
                    f"for this opportunity. Only one stakeholder can have "
                    f"the {role} role."
                )

        stakeholder.tags = [tags[n] for n in names]
        stakeholder.is_decision_maker = ("Decision Maker" in names)
    @staticmethod
    def create_stakeholder(data,user,active_role):
        opp=Stakeholder.query.session.get(__import__("app.models.opportunity.opportunity",fromlist=["Opportunity"]).Opportunity,data["opportunity_id"])
        if not opp: return None
        if not AuthorizationService.can_mutate_related(user,active_role,opp,"stakeholder","create"):
            raise AuthorizationDenied("You are not authorized to create stakeholders for this opportunity.")
        _validate_phone(data.get("phone"))

        account = db.session.get(Account, opp.account_id)
        if not account:
            raise ValueError("The opportunity must have an associated account before adding a stakeholder.")

        st=Stakeholder(name=data["name"],job_title=data.get("job_title"),email=data.get("email"),phone=data.get("phone"),company=account.account_name,notes=data.get("notes"),opportunity_id=opp.opportunity_id)
        try:
            db.session.add(st); db.session.flush(); StakeholderService._set_tags(st,data.get("tags",[]))
            ActivityService.log("Stakeholder",st.stakeholder_id,"STAKEHOLDER_CREATED",f"Stakeholder '{st.name}' created.",user.user_id,commit=False,active_role=active_role)
            db.session.commit(); return st
        except IntegrityError:
            db.session.rollback(); raise ValueError("Only one Decision Maker may exist per Opportunity.")
    @staticmethod
    def get_by_id(stakeholder_id,user,active_role):
        st=db.session.get(Stakeholder, stakeholder_id); return st if st and AuthorizationService.can_view_stakeholder(user,active_role,st) else None
    @staticmethod
    def get_by_opportunity(opportunity_id,user,active_role):
        from app.models.opportunity.opportunity import Opportunity
        opp=db.session.get(Opportunity, opportunity_id)
        return Stakeholder.query.filter_by(opportunity_id=opportunity_id).all() if opp and AuthorizationService.can_view_opportunity(user,active_role,opp) else []
    @staticmethod
    def update_stakeholder(stakeholder_id,data,user,active_role):
        data = dict(data or {})
        try:
            expected_version = int(data.pop("expected_version"))
        except (TypeError, ValueError):
            raise ValueError("expected_version is required and must be an integer.")

        st = (
            Stakeholder.query.filter_by(stakeholder_id=stakeholder_id)
            .with_for_update().first()
        )
        if not st:
            return None

        identity_fields = {"name", "job_title", "email", "phone", "company", "notes"}
        tags_only = "tags" in data and not any(k in data for k in identity_fields)
        action = "set_tags" if tags_only else "update"
        if not AuthorizationService.can_mutate_related(
            user, active_role, st.opportunity, "stakeholder", action
        ):
            raise AuthorizationDenied("You are not authorized to update this stakeholder.")
        if st.opportunity.operational_status == "Closed":
            raise AuthorizationDenied("Closed opportunities are locked.")
        if active_role == SALES_EXECUTIVE and any(
            k in data for k in {"name", "job_title", "email", "phone", "company"}
        ):
            raise AuthorizationDenied("Sales Executive cannot edit stakeholder identity fields.")
        if "phone" in data:
            _validate_phone(data["phone"])

        opportunity = st.opportunity
        result = db.session.execute(
            update(Opportunity)
            .where(
                Opportunity.opportunity_id == opportunity.opportunity_id,
                Opportunity.row_version == expected_version,
                Opportunity.operational_status != "Closed",
            )
            .values(
                row_version=Opportunity.row_version + 1,
                updated_at=datetime.utcnow(),
            )
        )
        if result.rowcount != 1:
            db.session.rollback()
            raise TransitionConflict("Opportunity version is stale. Refresh before retrying.")
        for key in ("name", "job_title", "email", "phone", "company", "notes"):
            if key in data:
                setattr(st, key, data[key])
        if "tags" in data:
            StakeholderService._set_tags(st, data["tags"])
        from app.services.activity_service import ActivityService
        ActivityService.log(
            "Stakeholder", st.stakeholder_id, "STAKEHOLDER_UPDATED",
            f"Stakeholder '{st.name}' updated.", user.user_id,
            commit=False, active_role=active_role,
        )
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return st

    @staticmethod
    def delete_stakeholder(stakeholder_id,user,active_role):
        st=db.session.get(Stakeholder, stakeholder_id)
        if not st: return False
        if not AuthorizationService.can_mutate_related(user,active_role,st.opportunity,"stakeholder","delete"): raise AuthorizationDenied("You are not authorized to delete this stakeholder.")
        db.session.delete(st); db.session.commit(); return True
