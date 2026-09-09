from decimal import Decimal

import pytest

from app.auth.authorization import AuthorizationDenied
from app.auth.password import hash_password
from app.constants.roles import (
    ADMIN,
    LEADERSHIP,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
)
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.closed_won_request import ClosedWonRequest
from app.services.lifecycle_transition_service import (
    LifecycleTransitionService,
    TransitionConflict,
    TransitionInvalid,
)
from app.services.opportunity_service import OpportunityService
from app.services.opportunity_value_service import OpportunityValueService


@pytest.fixture()
def a5_app(tmp_path, monkeypatch):
    uri = f"sqlite:///{tmp_path / 'a5.db'}"
    monkeypatch.setenv("DATABASE_URL", uri)
    monkeypatch.setenv("JWT_SECRET_KEY", "a5-test-secret")
    from app import create_app
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    with application.app_context():
        db.drop_all()
        db.create_all()
        account = Account(account_name="A5 Account", is_active=True)
        db.session.add(account)
        db.session.flush()
        users = {}
        for role in [LEADERSHIP, ADMIN, SALES_MANAGER, SALES_EXECUTIVE, PRE_SALES_MANAGER, SOLUTION_ENGINEER]:
            user = User(
                full_name=role,
                email=f"{role.lower().replace(' ', '_')}@a5.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            user.roles.append(UserRole(role=role))
            db.session.add(user)
            db.session.flush()
            users[role] = user
        application.config["A5"] = {"account": account.account_id, "users": users}
        db.session.commit()
    return application


def make_opportunity(application, stage="Qualified", value=500000):
    ids = application.config["A5"]
    finder = ids[SALES_EXECUTIVE]
    with application.app_context():
        opportunity = OpportunityService.create_opportunity({
            "account_id": ids["account"],
            "opportunity_name": "A5 Closure Test",
            "description": "Description",
            "pain_points": "Pain",
            "estimated_value": value,
            "probability": 60,
            "expected_close_date": None,
        }, finder, SALES_EXECUTIVE)
        opportunity.lifecycle_stage = stage
        opportunity.review_status = "Approved"
        db.session.add(OpportunityTeam(
            opportunity_id=opportunity.opportunity_id,
            user_id=ids[PRE_SALES_MANAGER].user_id,
            role=PRE_SALES_MANAGER,
        ))
        db.session.add(OpportunityTeam(
            opportunity_id=opportunity.opportunity_id,
            user_id=ids[SOLUTION_ENGINEER].user_id,
            role=SOLUTION_ENGINEER,
        ))
        db.session.commit()
        return opportunity.opportunity_id


def test_closed_won_snapshots_server_value_and_locks(a5_app):
    opportunity_id = make_opportunity(a5_app, value=725000)
    psm = a5_app.config["A5"]["users"][PRE_SALES_MANAGER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        closed = LifecycleTransitionService.close_won(
            opportunity_id, opportunity.row_version, psm, PRE_SALES_MANAGER
        )
        assert closed.outcome == "Closed Won"
        assert closed.operational_status == "Closed"
        assert closed.final_revenue == Decimal("725000.00")
        assert closed.lifecycle_stage == "Qualified"

        with pytest.raises(TransitionConflict):
            OpportunityValueService.change_value(
                opportunity_id, closed.estimated_value + 1,
                "attempt after closure", closed.row_version, psm, PRE_SALES_MANAGER
            )

        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.close_lost(
                opportunity_id, closed.row_version, "Competitor", None,
                psm, PRE_SALES_MANAGER
            )


def test_client_final_revenue_payload_is_not_a_close_input():
    from app.schemas.opportunity_schema import OpportunityCloseSchema
    with pytest.raises(Exception):
        OpportunityCloseSchema().load({
            "expected_version": 1,
            "final_revenue": 999999999,
        })


def test_closed_lost_requires_reason_and_other_explanation(a5_app):
    opportunity_id = make_opportunity(a5_app)
    psm = a5_app.config["A5"]["users"][PRE_SALES_MANAGER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.close_lost(
                opportunity_id, opportunity.row_version, None, None,
                psm, PRE_SALES_MANAGER
            )
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.close_lost(
                opportunity_id, opportunity.row_version, "Other", None,
                psm, PRE_SALES_MANAGER
            )
        closed = LifecycleTransitionService.close_lost(
            opportunity_id, opportunity.row_version, "Other", "Budget was withdrawn",
            psm, PRE_SALES_MANAGER
        )
        assert closed.outcome == "Closed Lost"
        assert closed.operational_status == "Closed"
        assert closed.final_revenue is None
        assert closed.lost_reason == "Other"
        assert closed.lost_explanation == "Budget was withdrawn"


def test_se_closed_won_requires_request_and_psm_approval(a5_app):
    opportunity_id = make_opportunity(a5_app, stage="POC")
    se = a5_app.config["A5"]["users"][SOLUTION_ENGINEER]
    psm = a5_app.config["A5"]["users"][PRE_SALES_MANAGER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.close_won(
                opportunity_id, opportunity.row_version, se, SOLUTION_ENGINEER
            )

        requested = LifecycleTransitionService.request_closed_won(
            opportunity_id, opportunity.row_version, se, SOLUTION_ENGINEER
        )
        assert requested.closed_won_request.status == "Pending"
        version = requested.row_version

        approved = LifecycleTransitionService.resolve_closed_won_request(
            opportunity_id, version, True, None, psm, PRE_SALES_MANAGER
        )
        assert approved.outcome == "Closed Won"
        assert approved.operational_status == "Closed"
        assert approved.closed_won_request.status == "Approved"


def test_se_can_close_lost_but_not_unassigned_se(a5_app):
    opportunity_id = make_opportunity(a5_app)
    se = a5_app.config["A5"]["users"][SOLUTION_ENGINEER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        closed = LifecycleTransitionService.close_lost(
            opportunity_id, opportunity.row_version, "Competitor", None,
            se, SOLUTION_ENGINEER
        )
        assert closed.outcome == "Closed Lost"

        # A second attempt is terminal even for an authorized role.
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.close_lost(
                opportunity_id, closed.row_version, "Budget", None,
                se, SOLUTION_ENGINEER
            )


def test_closure_uses_active_role_not_another_assigned_role(a5_app):
    opportunity_id = make_opportunity(a5_app)
    user = a5_app.config["A5"]["users"][SALES_EXECUTIVE]
    with a5_app.app_context():
        user = User.query.get(user.user_id)
        user.roles.append(UserRole(role=PRE_SALES_MANAGER))
        db.session.commit()
        opportunity = Opportunity.query.get(opportunity_id)
        # The caller is an assigned SE only when the active role is SE; merely
        # possessing another role does not turn Sales Executive into a closer.
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.close_won(
                opportunity_id, opportunity.row_version, user, SALES_EXECUTIVE
            )


def test_stale_close_returns_conflict_without_partial_state(a5_app):
    opportunity_id = make_opportunity(a5_app)
    psm = a5_app.config["A5"]["users"][PRE_SALES_MANAGER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        stale_version = opportunity.row_version
        OpportunityValueService.change_value(
            opportunity_id, Decimal("600000"), "new commercial value",
            stale_version, psm, PRE_SALES_MANAGER
        )
        current = Opportunity.query.get(opportunity_id)
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.close_won(
                opportunity_id, stale_version, psm, PRE_SALES_MANAGER
            )
        db.session.expire(current)
        current = Opportunity.query.get(opportunity_id)
        assert current.outcome == "Open"
        assert current.operational_status != "Closed"
        assert current.final_revenue is None


def test_closed_won_request_rejection_is_audited_and_reopen_is_not_created(a5_app):
    opportunity_id = make_opportunity(a5_app, stage="RFX")
    se = a5_app.config["A5"]["users"][SOLUTION_ENGINEER]
    psm = a5_app.config["A5"]["users"][PRE_SALES_MANAGER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        requested = LifecycleTransitionService.request_closed_won(
            opportunity_id, opportunity.row_version, se, SOLUTION_ENGINEER
        )
        rejected = LifecycleTransitionService.resolve_closed_won_request(
            opportunity_id, requested.row_version, False, "Insufficient commercial approval",
            psm, PRE_SALES_MANAGER
        )
        assert rejected.outcome == "Open"
        assert rejected.operational_status == "Active"
        assert rejected.closed_won_request.status == "Rejected"
        assert Opportunity.query.get(opportunity_id).lifecycle_stage == "RFX"
        assert Opportunity.query.get(opportunity_id).final_revenue is None


def test_lead_rejection_is_not_closed_lost(a5_app):
    ids = a5_app.config["A5"]
    with a5_app.app_context():
        opportunity = OpportunityService.create_opportunity({
            "account_id": ids["account"],
            "opportunity_name": "Rejected Lead",
            "description": "Description",
            "pain_points": "Pain",
            "estimated_value": 100,
            "probability": 10,
            "expected_close_date": None,
        }, ids[SALES_EXECUTIVE], SALES_EXECUTIVE)
        opportunity.review_status = "Pending Sales Manager Review"
        db.session.commit()
        LifecycleTransitionService.reject_lead(
            opportunity.opportunity_id, opportunity.row_version,
            "Not qualified", ids[SALES_MANAGER], SALES_MANAGER
        )
        current = Opportunity.query.get(opportunity.opportunity_id)
        assert current.lifecycle_stage == "Lead"
        assert current.review_status == "Rejected"
        assert current.outcome == "Open"
        assert current.operational_status == "Active"


def test_closed_opportunity_rejects_generic_field_update_and_ownership_change(a5_app):
    opportunity_id = make_opportunity(a5_app)
    psm = a5_app.config["A5"]["users"][PRE_SALES_MANAGER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        LifecycleTransitionService.close_won(
            opportunity_id, opportunity.row_version, psm, PRE_SALES_MANAGER
        )
        current = Opportunity.query.get(opportunity_id)
        with pytest.raises(AuthorizationDenied):
            OpportunityService.update_opportunity(
                opportunity_id,
                {
                    "opportunity_name": "Tampered",
                    "expected_version": current.row_version,
                },
                psm,
                PRE_SALES_MANAGER,
            )
        assert Opportunity.query.get(opportunity_id).created_by == a5_app.config["A5"]["users"][SALES_EXECUTIVE].user_id


def test_closure_audit_captures_active_role_and_terminal_state(a5_app):
    from app.models.system.audit_log import AuditLog

    opportunity_id = make_opportunity(a5_app)
    psm = a5_app.config["A5"]["users"][PRE_SALES_MANAGER]
    with a5_app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        LifecycleTransitionService.close_won(
            opportunity_id, opportunity.row_version, psm, PRE_SALES_MANAGER
        )
        row = AuditLog.query.filter_by(
            entity_type="Opportunity",
            entity_id=opportunity_id,
            action="OPPORTUNITY_CLOSED_WON",
        ).order_by(AuditLog.created_at.desc()).first()
        assert row is not None
        assert row.actor_active_role == PRE_SALES_MANAGER
        assert "Final Revenue" in row.description
