from flask import Blueprint, g, request

from app.auth.authorization import phase2_auth_required
from app.controllers.search_controller import SearchController

search_bp = Blueprint("search", __name__, url_prefix="/api/search")


@search_bp.get("")
@phase2_auth_required
def search():
    return SearchController.search(
        g.auth_user,
        g.active_role,
        request.args.get("q", ""),
        request.args.get("type"),
    )
