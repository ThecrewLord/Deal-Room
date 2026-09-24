from flask import jsonify

from app.services.search_service import SearchService


class SearchController:
    @staticmethod
    def search(user, active_role, query_text, entity_type=None, **filters):
        try:
            result = SearchService.search(
                query_text, user, active_role, entity_type, **filters
            )
            return jsonify(result), 200
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 400
