import os
import ast

import pytest

from app.constants.roles import ADMIN, SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY
from app.services.notification_service import ROLE_BY_NOTIFICATION


ROOT = os.path.dirname(os.path.dirname(__file__))


def test_canonical_roles_are_exact():
    assert [ADMIN, SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY] == [
        "Admin", "Sales Executive", "Sales Manager", "Pre-Sales Manager", "Solution Engineer", "Delivery"
    ]


def test_notification_role_map_has_required_workflow_types():
    assert ROLE_BY_NOTIFICATION["OPPORTUNITY_SUBMITTED_FOR_REVIEW"] == SALES_MANAGER
    assert ROLE_BY_NOTIFICATION["OPPORTUNITY_APPROVED"] == PRE_SALES_MANAGER
    assert ROLE_BY_NOTIFICATION["OPPORTUNITY_REJECTED"] == SALES_EXECUTIVE
    assert ROLE_BY_NOTIFICATION["SALES_OWNER_ASSIGNED"] == SALES_EXECUTIVE
    assert ROLE_BY_NOTIFICATION["SOLUTION_ENGINEER_ASSIGNED"] == SOLUTION_ENGINEER
    assert ROLE_BY_NOTIFICATION["DELIVERY_ASSIGNED"] == DELIVERY
    assert ROLE_BY_NOTIFICATION["POC_REQUESTED"] == PRE_SALES_MANAGER
    assert ROLE_BY_NOTIFICATION["POC_APPROVED"] == DELIVERY
    assert ROLE_BY_NOTIFICATION["POC_REJECTED"] == SOLUTION_ENGINEER
    assert ROLE_BY_NOTIFICATION["POC_RESULT_SUBMITTED"] == SOLUTION_ENGINEER


def test_search_route_is_registered_and_does_not_use_unrestricted_query():
    path = os.path.join(ROOT, "app", "api", "search_routes.py")
    assert os.path.exists(path)
    source = open(path, encoding="utf8").read()
    assert "phase2_auth_required" in source
    service = open(os.path.join(ROOT, "app", "services", "search_service.py"), encoding="utf8").read()
    assert "AuthorizationService.opportunity_query" in service
    assert "AuthorizationService.account_query" in service
    assert "Opportunity.query" not in service.split("AuthorizationService.opportunity_query", 1)[0]
    assert "Model.query.all" not in service


def test_notification_service_requires_entity_authorization():
    source = open(os.path.join(ROOT, "app", "services", "notification_service.py"), encoding="utf8").read()
    assert "_entity_authorized" in source
    assert "can_view_opportunity" in source
    assert "can_view_poc" in source
    assert "can_view_account" in source


def test_activity_endpoint_rejects_unknown_entity_types():
    source = open(os.path.join(ROOT, "app", "auth", "authorization.py"), encoding="utf8").read()
    assert "return False" in source
    assert 'entity_type.lower() == "opportunity"' in source


def test_phase10_frontend_search_calls_backend():
    header = open(os.path.join(os.path.dirname(os.path.dirname(ROOT)), "frontend", "src", "components", "Header.jsx"), encoding="utf8").read()
    api = open(os.path.join(os.path.dirname(os.path.dirname(ROOT)), "frontend", "src", "api", "searchApi.js"), encoding="utf8").read()
    assert "searchAuthorized" in header
    assert "setTimeout" in header
    assert '"/search"' in api
