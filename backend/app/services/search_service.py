from sqlalchemy import or_, cast, String

from app.auth.authorization import AuthorizationService
from app.constants.roles import ADMIN
from app.models.account.account import Account
from app.models.account.oem_partner import OEMPartner
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.poc_tracker import POCTracker
from app.models.phase2 import Activity, FollowUp, DeliveryProject, OEMOpportunity


class SearchService:
    """Authorized PostgreSQL-backed global search.

    Search is deliberately a read model over existing domains. It never creates
    duplicate search records and every entity query starts from the central
    authorization scope before restricted fields are projected.
    """

    MAX_QUERY_LENGTH = 100
    MIN_QUERY_LENGTH = 2
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 50
    TYPES = {
        "opportunity", "account", "stakeholder", "oem", "activity",
        "follow-up", "delivery-project", "poc",
    }

    @staticmethod
    def _validate(query_text, entity_type, page, page_size):
        query_text = (query_text or "").strip()
        if len(query_text) < SearchService.MIN_QUERY_LENGTH:
            raise ValueError("Search query must contain at least 2 characters.")
        if len(query_text) > SearchService.MAX_QUERY_LENGTH:
            raise ValueError("Search query is too long.")

        if entity_type:
            entity_type = entity_type.strip().lower()
            aliases = {
                "followup": "follow-up",
                "follow_ups": "follow-up",
                "delivery_project": "delivery-project",
                "delivery": "delivery-project",
            }
            entity_type = aliases.get(entity_type, entity_type)
            if entity_type not in SearchService.TYPES:
                raise ValueError("Invalid search type.")

        try:
            page = int(page)
            page_size = int(page_size)
        except (TypeError, ValueError):
            raise ValueError("page and page_size must be integers.")
        if page < 1:
            raise ValueError("page must be at least 1.")
        if page_size < 1 or page_size > SearchService.MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {SearchService.MAX_PAGE_SIZE}.")
        return query_text, entity_type, page, page_size

    @staticmethod
    def _opportunity_scope(user, active_role, stage=None, status=None, account_id=None, owner_id=None):
        query = AuthorizationService.opportunity_query(user, active_role)
        if stage:
            query = query.filter(Opportunity.lifecycle_stage == stage)
        if status:
            query = query.filter(Opportunity.operational_status == status)
        if account_id is not None:
            try:
                account_id = int(account_id)
            except (TypeError, ValueError):
                raise ValueError("account_id must be an integer.")
            query = query.filter(Opportunity.account_id == account_id)
        if owner_id is not None:
            try:
                owner_id = int(owner_id)
            except (TypeError, ValueError):
                raise ValueError("owner_id must be an integer.")
            query = query.filter(Opportunity.sales_owner_id == owner_id)
        return query

    @staticmethod
    def _project(entity_type, entity, opportunity=None):
        base = {
            "type": entity_type,
            "id": getattr(entity, "opportunity_id", None)
            if entity_type == "opportunity"
            else getattr(entity, "account_id", None)
            if entity_type == "account"
            else getattr(entity, "stakeholder_id", None)
            if entity_type == "stakeholder"
            else getattr(entity, "oem_partner_id", None)
            if entity_type == "oem"
            else getattr(entity, "activity_id", None)
            if entity_type == "activity"
            else getattr(entity, "follow_up_id", None)
            if entity_type == "follow-up"
            else getattr(entity, "delivery_project_id", None)
            if entity_type == "delivery-project"
            else getattr(entity, "poc_id", None),
        }
        if entity_type == "opportunity":
            base.update(title=entity.opportunity_name, subtitle=entity.account.account_name if entity.account else None,
                        stage=entity.lifecycle_stage, status=entity.operational_status, outcome=entity.outcome,
                        updated_at=entity.updated_at)
        elif entity_type == "account":
            base.update(title=entity.account_name, subtitle=entity.industry, updated_at=entity.updated_at)
        elif entity_type == "stakeholder":
            base.update(title=entity.name, subtitle=entity.company or (opportunity.account.account_name if opportunity and opportunity.account else None),
                        updated_at=entity.updated_at)
        elif entity_type == "oem":
            # Employee-facing search intentionally projects only non-sensitive OEM identity.
            base.update(title=entity.partner_name, subtitle=entity.product_name, updated_at=entity.updated_at)
        elif entity_type == "activity":
            base.update(title=entity.summary, subtitle=opportunity.opportunity_name if opportunity else None,
                        activity_type=entity.activity_type, actor=entity.actor.full_name if entity.actor else None,
                        updated_at=entity.created_at)
        elif entity_type == "follow-up":
            base.update(title=entity.description, subtitle=opportunity.opportunity_name if opportunity else None,
                        owner=entity.owner.full_name if entity.owner else None, status=entity.status,
                        due_date=entity.due_date, updated_at=entity.updated_at)
        elif entity_type == "delivery-project":
            base.update(title=f"Delivery Project #{entity.delivery_project_id}",
                        subtitle=opportunity.opportunity_name if opportunity else None,
                        status=entity.status, updated_at=entity.updated_at)
        elif entity_type == "poc":
            base.update(title=entity.poc_name, subtitle=opportunity.opportunity_name if opportunity else None,
                        status=entity.status, updated_at=entity.updated_at)
        return base

    @classmethod
    def search(cls, query_text, user, active_role, entity_type=None, *,
               stage=None, status=None, account_id=None, owner_id=None,
               page=1, page_size=20):
        query_text, entity_type, page, page_size = cls._validate(
            query_text, entity_type, page, page_size
        )

        if active_role == ADMIN:
            return {"items": [], "page": page, "page_size": page_size, "total": 0}

        pattern = f"%{query_text}%"
        opp_scope = cls._opportunity_scope(
            user, active_role, stage=stage, status=status,
            account_id=account_id, owner_id=owner_id,
        )
        visible_ids = opp_scope.with_entities(Opportunity.opportunity_id).subquery()
        items = []

        if entity_type in (None, "opportunity"):
            q = opp_scope.filter(or_(
                Opportunity.opportunity_name.ilike(pattern),
                Opportunity.description.ilike(pattern),
                cast(Opportunity.opportunity_id, String).ilike(pattern),
                Opportunity.lifecycle_stage.ilike(pattern),
                Opportunity.operational_status.ilike(pattern),
                Opportunity.outcome.ilike(pattern),
            )).order_by(Opportunity.updated_at.desc(), Opportunity.opportunity_id.desc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("opportunity", row))

        if entity_type in (None, "account"):
            q = AuthorizationService.account_query(user, active_role).filter(
                Account.account_name.ilike(pattern)
            ).order_by(Account.account_name.asc(), Account.account_id.asc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("account", row))

        if entity_type in (None, "stakeholder"):
            q = Stakeholder.query.filter(
                Stakeholder.opportunity_id.in_(visible_ids),
                or_(
                    Stakeholder.name.ilike(pattern),
                    Stakeholder.job_title.ilike(pattern),
                    Stakeholder.company.ilike(pattern),
                ),
            ).order_by(Stakeholder.updated_at.desc(), Stakeholder.stakeholder_id.desc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("stakeholder", row, row.opportunity))

        if entity_type in (None, "oem"):
            q = OEMPartner.query.join(
                OEMOpportunity, OEMOpportunity.oem_partner_id == OEMPartner.oem_partner_id
            ).filter(
                OEMOpportunity.opportunity_id.in_(visible_ids),
                or_(
                    OEMPartner.partner_name.ilike(pattern),
                    OEMPartner.product_name.ilike(pattern),
                ),
            ).distinct().order_by(OEMPartner.partner_name.asc(), OEMPartner.oem_partner_id.asc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("oem", row))

        if entity_type in (None, "activity"):
            q = Activity.query.filter(
                Activity.opportunity_id.in_(visible_ids),
                or_(
                    Activity.summary.ilike(pattern),
                    Activity.activity_type.ilike(pattern),
                ),
            ).order_by(Activity.created_at.desc(), Activity.activity_id.desc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("activity", row, row.opportunity))

        if entity_type in (None, "follow-up"):
            q = FollowUp.query.filter(
                FollowUp.opportunity_id.in_(visible_ids),
                FollowUp.description.ilike(pattern),
            ).order_by(FollowUp.due_date.asc(), FollowUp.follow_up_id.asc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("follow-up", row, row.opportunity))

        if entity_type in (None, "delivery-project"):
            q = DeliveryProject.query.filter(
                DeliveryProject.opportunity_id.in_(visible_ids),
                or_(
                    cast(DeliveryProject.delivery_project_id, String).ilike(pattern),
                    DeliveryProject.status.ilike(pattern),
                ),
            ).order_by(DeliveryProject.updated_at.desc(), DeliveryProject.delivery_project_id.desc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("delivery-project", row, row.opportunity))

        if entity_type in (None, "poc"):
            q = POCTracker.query.filter(
                POCTracker.opportunity_id.in_(visible_ids),
                or_(
                    POCTracker.poc_name.ilike(pattern),
                    POCTracker.objective.ilike(pattern),
                ),
            ).order_by(POCTracker.updated_at.desc(), POCTracker.poc_id.desc())
            for row in q.limit(cls.MAX_PAGE_SIZE * 2).all():
                items.append(cls._project("poc", row, row.opportunity))

        # Mixed search has no cross-entity natural ordering, so use the source
        # update timestamp and then a stable id. This gives deterministic pages.
        items.sort(key=lambda x: (str(x.get("updated_at") or ""), int(x["id"] or 0)), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start:start + page_size],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": start + page_size < total,
        }
