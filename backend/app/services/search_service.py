from sqlalchemy import or_

from app.auth.authorization import AuthorizationService
from app.constants.roles import ADMIN
from app.models.account.account import Account
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker


class SearchService:
    """Server-side search that applies the exact same visibility query used by lists."""

    MAX_RESULTS = 25
    MAX_QUERY_LENGTH = 100
    MIN_QUERY_LENGTH = 2
    TYPES = {"opportunity", "account", "poc"}

    @staticmethod
    def search(query_text, user, active_role, entity_type=None):
        query_text = (query_text or "").strip()
        if len(query_text) < SearchService.MIN_QUERY_LENGTH:
            raise ValueError("Search query must contain at least 2 characters.")
        if len(query_text) > SearchService.MAX_QUERY_LENGTH:
            raise ValueError("Search query is too long.")

        if entity_type:
            entity_type = entity_type.strip().lower()
            if entity_type not in SearchService.TYPES:
                raise ValueError("Invalid search type.")

        # Admin is intentionally not a business-data viewer.
        if active_role == ADMIN:
            return []

        pattern = f"%{query_text}%"
        results = []

        if entity_type in (None, "opportunity"):
            opportunities = (
                AuthorizationService.opportunity_query(user, active_role)
                .filter(or_(
                    Opportunity.opportunity_name.ilike(pattern),
                    Opportunity.description.ilike(pattern),
                ))
                .order_by(Opportunity.updated_at.desc())
                .limit(SearchService.MAX_RESULTS)
                .all()
            )
            results.extend({
                "type": "opportunity",
                "id": item.opportunity_id,
                "title": item.opportunity_name,
                "subtitle": item.account.account_name if item.account else None,
            } for item in opportunities)

        if entity_type in (None, "account"):
            accounts = (
                AuthorizationService.account_query(user, active_role)
                .filter(Account.account_name.ilike(pattern))
                .order_by(Account.account_name.asc())
                .limit(SearchService.MAX_RESULTS)
                .all()
            )
            results.extend({
                "type": "account",
                "id": item.account_id,
                "title": item.account_name,
                "subtitle": item.industry,
            } for item in accounts)

        if entity_type in (None, "poc"):
            visible_opportunity_ids = AuthorizationService.opportunity_query(
                user, active_role
            ).with_entities(Opportunity.opportunity_id).subquery()
            pocs = (
                POCTracker.query
                .filter(POCTracker.opportunity_id.in_(visible_opportunity_ids))
                .filter(or_(
                    POCTracker.poc_name.ilike(pattern),
                    POCTracker.objective.ilike(pattern),
                ))
                .order_by(POCTracker.updated_at.desc())
                .limit(SearchService.MAX_RESULTS)
                .all()
            )
            results.extend({
                "type": "poc",
                "id": item.poc_id,
                "title": item.poc_name,
                "subtitle": item.opportunity.opportunity_name if item.opportunity else None,
            } for item in pocs)

        return results[:SearchService.MAX_RESULTS]
