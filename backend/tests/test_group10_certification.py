"""Group 10 regression/security certification tests.

These tests intentionally target integration boundaries rather than introducing
new business behavior.  They complement the existing Groups 1-9 suites.
"""
from pathlib import Path

import pytest
from marshmallow import ValidationError

from app import create_app
from app.schemas.opportunity_schema import OpportunityUpdateSchema


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'group10.db'}",
        "JWT_SECRET_KEY": "group10-secret",
    })
    return app


def test_obsolete_closed_won_routes_are_not_registered(app):
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/api/opportunities/<int:opportunity_id>/request-closed-won" not in routes
    assert "/api/opportunities/<int:opportunity_id>/approve-closed-won" not in routes
    assert "/api/opportunities/<int:opportunity_id>/reject-closed-won" not in routes


def test_client_cannot_control_authoritative_workflow_fields():
    schema = OpportunityUpdateSchema()
    with pytest.raises(ValidationError):
        schema.load({
            "lifecycle_stage": "Delivery",
            "expected_version": 1,
        })
    with pytest.raises(ValidationError):
        schema.load({
            "outcome": "Closed Won",
            "expected_version": 1,
        })
    with pytest.raises(ValidationError):
        schema.load({
            "operational_status": "Closed",
            "expected_version": 1,
        })
    with pytest.raises(ValidationError):
        schema.load({
            "deal_finder_id": 999,
            "expected_version": 1,
        })


def test_group10_migration_graph_has_one_head():
    versions_dir = Path(__file__).resolve().parents[1] / "migrations" / "versions"
    revisions = {}
    for path in versions_dir.glob("*.py"):
        source = path.read_text()
        namespace = {}
        exec(compile(source, str(path), "exec"), namespace)
        revisions[namespace["revision"]] = namespace.get("down_revision")

    referenced = set()
    for down_revision in revisions.values():
        if isinstance(down_revision, (tuple, list)):
            referenced.update(down_revision)
        elif down_revision:
            referenced.add(down_revision)

    heads = [revision for revision in revisions if revision not in referenced]
    assert heads == ["a1c2d3e4f5g6"]


def test_no_legacy_closed_won_compatibility_symbols_remain_in_application_code():
    root = Path(__file__).resolve().parents[1] / "app"
    forbidden = {
        "request-closed-won",
        "approve-closed-won",
        "reject-closed-won",
        "request_closed_won",
        "resolve_closed_won",
        "can_request_closed_won",
        "can_approve_closed_won_request",
    }
    matches = []
    for path in root.rglob("*.py"):
        text = path.read_text()
        for token in forbidden:
            if token in text:
                matches.append(f"{path}:{token}")
    assert matches == []
