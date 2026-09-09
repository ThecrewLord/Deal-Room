from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.auth.password import hash_password
from app.constants.roles import (
    ADMIN, DATA_ANALYST, DEVOPS_ENGINEER, DELIVERY_MANAGER, LEADERSHIP,
    PRE_SALES_MANAGER, SALES_EXECUTIVE, SALES_MANAGER, SOLUTION_ENGINEER,
)
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.opportunity_value_history import OpportunityValueHistory
from app.services.lifecycle_transition_service import LifecycleTransitionService, TransitionConflict
from app.services.opportunity_service import OpportunityService
from app.services.opportunity_value_service import OpportunityValueService, RevenueAttributionService


@pytest.fixture()
def a4_app(tmp_path, monkeypatch):
    uri = f"sqlite:///{tmp_path / 'a4.db'}"
    monkeypatch.setenv("DATABASE_URL", uri)
    monkeypatch.setenv("JWT_SECRET_KEY", "a4-test-secret")
    from app import create_app
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    with application.app_context():
        db.drop_all()
        db.create_all()
        account = Account(account_name="A4 Account", is_active=True)
        db.session.add(account)
        db.session.flush()
        users = {}
        for role in [
            LEADERSHIP, ADMIN, SALES_MANAGER, SALES_EXECUTIVE, PRE_SALES_MANAGER,
            SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST,
        ]:
            user = User(
                full_name=role,
                email=f"{role.lower().replace(' ', '_')}@a4.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            user.roles.append(UserRole(role=role))
            db.session.add(user)
            db.session.flush()
            users[role] = user
        application.config["A4"] = {"account": account.account_id, "users": users}
        db.session.commit()
    return application


def make_opportunity(application, value=500000):
    ids = application.config["A4"]
    finder = ids["users"][SALES_EXECUTIVE]
    with application.app_context():
        opportunity = OpportunityService.create_opportunity({
            "account_id": ids["account"],
            "opportunity_name": "A4 Value Test",
            "description": "Description",
            "pain_points": "Pain",
            "estimated_value": value,
            "probability": 20,
            "expected_close_date": None,
        }, finder, SALES_EXECUTIVE)
        db.session.commit()
        return opportunity.opportunity_id


def test_initial_value_history_is_recorded_once(a4_app):
    opportunity_id = make_opportunity(a4_app)
    with a4_app.app_context():
        rows = OpportunityValueHistory.query.filter_by(opportunity_id=opportunity_id).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.old_value is None
        assert row.new_value == Decimal("500000.00")
        assert row.reason == "Initial Opportunity Value"
        assert row.actor_active_role == SALES_EXECUTIVE
        assert row.opportunity_row_version == 1


def test_authorized_value_change_is_atomic_and_versioned(a4_app):
    opportunity_id = make_opportunity(a4_app)
    manager = a4_app.config["A4"]["users"][SALES_MANAGER]
    with a4_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        updated = OpportunityValueService.change_value(
            opportunity_id, Decimal("750000.25"), "Updated after commercial review", 1, manager, SALES_MANAGER
        )
        assert updated.estimated_value == Decimal("750000.25")
        assert updated.row_version == 2
        rows = OpportunityValueHistory.query.filter_by(opportunity_id=opportunity_id).order_by(OpportunityValueHistory.history_id).all()
        assert len(rows) == 2
        assert rows[-1].old_value == Decimal("500000.00")
        assert rows[-1].new_value == Decimal("750000.25")
        assert rows[-1].reason == "Updated after commercial review"
        assert rows[-1].actor_id == manager.user_id
        assert rows[-1].actor_active_role == SALES_MANAGER
        assert rows[-1].opportunity_row_version == 2


def test_all_forbidden_roles_are_denied(a4_app):
    opportunity_id = make_opportunity(a4_app)
    ids = a4_app.config["A4"]
    with a4_app.app_context():
        # Give each business role resource visibility without granting value authority.
        opportunity = Opportunity.query.get(opportunity_id)
        opportunity.lifecycle_stage = "RFX"
        opportunity.review_status = "Approved"
        for role in [SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST]:
            db.session.add(OpportunityTeam(opportunity_id=opportunity_id, user_id=ids["users"][role].user_id, role=role))
        db.session.commit()
        for role in [SALES_EXECUTIVE, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST, ADMIN]:
            user = ids["users"][role]
            with pytest.raises(AuthorizationDenied):
                OpportunityValueService.change_value(
                    opportunity_id, Decimal("600000"), "Unauthorized attempt", opportunity.row_version, user, role
                )


def test_pre_sales_manager_and_leadership_can_change_value(a4_app):
    opportunity_id = make_opportunity(a4_app)
    ids = a4_app.config["A4"]
    with a4_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        opportunity.lifecycle_stage = "RFX"
        opportunity.review_status = "Approved"
        db.session.add(OpportunityTeam(opportunity_id=opportunity_id, user_id=ids[PRE_SALES_MANAGER].user_id, role=PRE_SALES_MANAGER))
        db.session.commit()
        psm = ids[PRE_SALES_MANAGER]
        updated = OpportunityValueService.change_value(opportunity_id, Decimal("600000"), "Technical scope changed", 1, psm, PRE_SALES_MANAGER)
        assert updated.row_version == 2
        leadership = ids[LEADERSHIP]
        updated = OpportunityValueService.change_value(opportunity_id, Decimal("650000"), "Leadership governance adjustment", 2, leadership, LEADERSHIP)
        assert updated.row_version == 3
        assert updated.estimated_value == Decimal("650000.00")


def test_active_role_isolation(a4_app):
    opportunity_id = make_opportunity(a4_app)
    ids = a4_app.config["A4"]
    with a4_app.app_context():
        user = ids[SALES_EXECUTIVE]
        user.roles.append(UserRole(role=SALES_MANAGER))
        db.session.add(OpportunityTeam(opportunity_id=opportunity_id, user_id=user.user_id, role=SALES_EXECUTIVE))
        db.session.commit()
        with pytest.raises(AuthorizationDenied):
            OpportunityValueService.change_value(opportunity_id, 700000, "Wrong active role", 1, user, SALES_EXECUTIVE)
        assert OpportunityValueService.change_value(opportunity_id, 700000, "Correct active role", 1, user, SALES_MANAGER).row_version == 2


def test_reason_is_mandatory_and_old_value_is_server_derived(a4_app):
    opportunity_id = make_opportunity(a4_app)
    manager = a4_app.config["A4"][SALES_MANAGER]
    with a4_app.app_context():
        with pytest.raises(ValueError):
            OpportunityValueService.change_value(opportunity_id, 700000, "", 1, manager, SALES_MANAGER)
        with pytest.raises(ValueError):
            OpportunityValueService.change_value(opportunity_id, 700000, "x", 1, manager, SALES_MANAGER)
        # A malicious old_value is never an accepted service argument.
        result = OpportunityValueService.change_value(opportunity_id, 700000, "Valid reason", 1, manager, SALES_MANAGER)
        row = OpportunityValueHistory.query.filter_by(opportunity_id=opportunity_id).order_by(OpportunityValueHistory.history_id.desc()).first()
        assert result.estimated_value == Decimal("700000.00")
        assert row.old_value == Decimal("500000.00")


def test_stale_version_returns_conflict_and_does_not_write_history(a4_app):
    opportunity_id = make_opportunity(a4_app)
    manager = a4_app.config["A4"][SALES_MANAGER]
    with a4_app.app_context():
        OpportunityValueService.change_value(opportunity_id, 700000, "First writer", 1, manager, SALES_MANAGER)
        with pytest.raises(TransitionConflict):
            OpportunityValueService.change_value(opportunity_id, 800000, "Stale writer", 1, manager, SALES_MANAGER)
        assert Opportunity.query.get(opportunity_id).estimated_value == Decimal("700000.00")
        assert OpportunityValueHistory.query.filter_by(opportunity_id=opportunity_id).count() == 2


def test_closed_opportunity_value_and_final_revenue_are_locked(a4_app):
    opportunity_id = make_opportunity(a4_app)
    ids = a4_app.config["A4"]
    with a4_app.app_context():
        finder = ids[SALES_EXECUTIVE]
        manager = ids[SALES_MANAGER]
        LifecycleTransitionService.submit_lead(opportunity_id, 1, finder, SALES_EXECUTIVE)
        LifecycleTransitionService.close_won(opportunity_id, 2, manager, SALES_MANAGER)
        opportunity = Opportunity.query.get(opportunity_id)
        assert opportunity.final_revenue == Decimal("500000.00")
        assert opportunity.operational_status == "Closed"
        with pytest.raises(AuthorizationDenied):
            OpportunityValueService.change_value(opportunity_id, 900000, "After close", opportunity.row_version, manager, SALES_MANAGER)
        original = opportunity.final_revenue
        opportunity.final_revenue = Decimal("999999999")
        # Generic public update schema never accepts final_revenue; service mutation is intentionally not provided.
        db.session.rollback()
        assert Opportunity.query.get(opportunity_id).final_revenue == original


def test_history_has_no_update_or_delete_api(a4_app):
    routes = {rule.rule for rule in a4_app.url_map.iter_rules()}
    assert not any("value-history" in rule and rule.methods.intersection({"PUT", "PATCH", "DELETE"}) for rule in a4_app.url_map.iter_rules())


def test_revenue_attribution_uses_final_revenue_and_deal_finder(a4_app):
    ids = a4_app.config["A4"]
    with a4_app.app_context():
        alice = ids[SALES_EXECUTIVE]
        bob = ids[SALES_MANAGER]
        a = OpportunityService.create_opportunity({"account_id": ids["account"], "opportunity_name": "A", "estimated_value": 100}, alice, SALES_EXECUTIVE)
        b = OpportunityService.create_opportunity({"account_id": ids["account"], "opportunity_name": "B", "estimated_value": 200}, bob, SALES_MANAGER)
        c = OpportunityService.create_opportunity({"account_id": ids["account"], "opportunity_name": "C", "estimated_value": 300}, alice, SALES_EXECUTIVE)
        db.session.add(OpportunityTeam(opportunity_id=b.opportunity_id, user_id=alice.user_id, role=SALES_EXECUTIVE))
        for o, revenue in [(a, 100), (b, 200)]:
            o.final_revenue = revenue
            o.outcome = "Closed Won"
            o.operational_status = "Closed"
        c.outcome = "Closed Lost"
        c.operational_status = "Closed"
        db.session.commit()
        report = RevenueAttributionService.for_sales_executive(alice, SALES_EXECUTIVE)
        assert report["sourced_revenue"] == 100.0
        assert report["participation_revenue"] == 300.0


def test_generic_update_schema_rejects_value_and_final_revenue_fields(a4_app):
    from marshmallow import ValidationError
    from app.schemas.opportunity_schema import OpportunityUpdateSchema
    with pytest.raises(ValidationError):
        OpportunityUpdateSchema().load({"estimated_value": 999, "expected_version": 1})
    with pytest.raises(ValidationError):
        OpportunityUpdateSchema().load({"final_revenue": 999, "expected_version": 1})
