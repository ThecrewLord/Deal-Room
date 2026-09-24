import os

from app.constants.roles import (
    ADMIN,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
    AVAILABLE_ROLES,
)
from app.services.notification_service import ROLE_BY_NOTIFICATION


ROOT = os.path.dirname(os.path.dirname(__file__))


def test_canonical_roles_are_exact():
    assert AVAILABLE_ROLES == [
        "Leadership",
        "Admin",
        "Sales Manager",
        "Sales Executive",
        "Pre-Sales Manager",
        "Solution Engineer",
        "Delivery Manager",
        "DevOps Engineer",
        "Data Analyst",
    ]

    assert [
        ADMIN,
        SALES_EXECUTIVE,
        SALES_MANAGER,
        PRE_SALES_MANAGER,
        SOLUTION_ENGINEER,
        DELIVERY_MANAGER,
        DEVOPS_ENGINEER,
        DATA_ANALYST,
    ] == [
        "Admin",
        "Sales Executive",
        "Sales Manager",
        "Pre-Sales Manager",
        "Solution Engineer",
        "Delivery Manager",
        "DevOps Engineer",
        "Data Analyst",
    ]


def test_notification_roles_match_workflow():
    assert ROLE_BY_NOTIFICATION["OPPORTUNITY_SUBMITTED_FOR_REVIEW"] == SALES_MANAGER
    assert ROLE_BY_NOTIFICATION["OPPORTUNITY_APPROVED"] == PRE_SALES_MANAGER
    assert ROLE_BY_NOTIFICATION["SALES_OWNER_ASSIGNED"] == SALES_EXECUTIVE
    assert ROLE_BY_NOTIFICATION["SOLUTION_ENGINEER_ASSIGNED"] == SOLUTION_ENGINEER
    assert ROLE_BY_NOTIFICATION["POC_REQUESTED"] == DELIVERY_MANAGER
    assert ROLE_BY_NOTIFICATION["POC_APPROVED"] == SOLUTION_ENGINEER
    assert ROLE_BY_NOTIFICATION["POC_REJECTED"] == SOLUTION_ENGINEER
    assert ROLE_BY_NOTIFICATION["POC_RESULT_SUBMITTED"] == SOLUTION_ENGINEER
    assert ROLE_BY_NOTIFICATION["CLOSED_WON_REQUESTED"] == PRE_SALES_MANAGER
    assert ROLE_BY_NOTIFICATION["CLOSED_WON_REQUEST_APPROVED"] == SOLUTION_ENGINEER
    assert ROLE_BY_NOTIFICATION["CLOSED_WON_REQUEST_REJECTED"] == SOLUTION_ENGINEER


def test_search_route_is_registered_and_scoped():
    path = os.path.join(ROOT, "app", "api", "search_routes.py")
    assert os.path.exists(path)

    source = open(path, encoding="utf8").read()
    assert "phase2_auth_required" in source

    service = open(
        os.path.join(ROOT, "app", "services", "search_service.py"),
        encoding="utf8",
    ).read()

    assert "AuthorizationService.opportunity_query" in service
    assert "AuthorizationService.account_query" in service
    assert "Opportunity.query" not in service.split(
        "AuthorizationService.opportunity_query",
        1,
    )[0]
    assert "Model.query.all" not in service


def test_notifications_require_entity_authorization():
    source = open(
        os.path.join(ROOT, "app", "services", "notification_service.py"),
        encoding="utf8",
    ).read()

    assert "_entity_authorized" in source
    assert "can_view_opportunity" in source
    assert "can_view_poc" in source
    assert "can_view_account" in source


def test_activity_endpoint_rejects_unknown_entities():
    source = open(
        os.path.join(ROOT, "app", "auth", "authorization.py"),
        encoding="utf8",
    ).read()

    assert "return False" in source
    assert 'entity_type.lower() == "opportunity"' in source


def test_frontend_search_calls_backend():
    project_root = os.path.dirname(ROOT)

    header_path = os.path.join(
        project_root,
        "frontend",
        "src",
        "components",
        "Header.jsx",
    )

    api_path = os.path.join(
        project_root,
        "frontend",
        "src",
        "api",
        "searchApi.js",
    )

    assert os.path.exists(header_path)
    assert os.path.exists(api_path)

    header = open(header_path, encoding="utf8").read()
    api = open(api_path, encoding="utf8").read()

    assert "searchAuthorized" in header
    assert "setTimeout" in header
    assert '"/search"' in api


def test_search_service_supports_phase3_entity_vocabulary():
    from app.services.search_service import SearchService
    assert SearchService.TYPES == {
        "opportunity", "account", "stakeholder", "oem", "activity",
        "follow-up", "delivery-project", "poc",
    }
    assert SearchService.MAX_PAGE_SIZE == 50


def test_search_result_projection_does_not_expose_oem_contacts():
    from app.services.search_service import SearchService
    from types import SimpleNamespace
    oem = SimpleNamespace(
        oem_partner_id=7, partner_name="Acme OEM", product_name="Platform",
        contact_person="Private Contact", email="private@example.com", phone="123",
        updated_at=None,
    )
    result = SearchService._project("oem", oem)
    assert result["title"] == "Acme OEM"
    assert "email" not in result and "phone" not in result and "contact_person" not in result
