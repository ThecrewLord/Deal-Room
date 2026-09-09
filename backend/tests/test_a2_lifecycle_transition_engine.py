import os
import pytest

from app import create_app
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
from app.auth.authorization import AuthorizationDenied
from app.services.lifecycle_transition_service import (
    LifecycleTransitionService, TransitionConflict, TransitionInvalid,
)


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'a2.db'}")
    monkeypatch.setenv("JWT_SECRET_KEY", "a2-test-secret")
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'a2.db'}"})
    with application.app_context():
        db.drop_all()
        db.create_all()
        account = Account(account_name="A2 Account")
        db.session.add(account)
        db.session.flush()

        users = {}
        roles = [
            LEADERSHIP, ADMIN, SALES_MANAGER, SALES_EXECUTIVE,
            PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER,
            DEVOPS_ENGINEER, DATA_ANALYST,
        ]
        for role in roles:
            u = User(
                full_name=role,
                email=f"{role.lower().replace(' ', '_')}@a2.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED", active=True,
            )
            u.roles.append(UserRole(role=role))
            db.session.add(u)
            db.session.flush()
            users[role] = u

        opp = Opportunity(
            account_id=account.account_id,
            created_by=users[SALES_EXECUTIVE].user_id,
            sales_owner_id=None,
            stage_id=1,
            opportunity_name="A2 Opportunity",
            lifecycle_stage="Lead",
            outcome="Open",
            operational_status="Active",
            review_status="Draft",
            row_version=1,
            status="Active",
            is_active=True,
        )
        db.session.add(opp)
        db.session.flush()
        db.session.add(OpportunityTeam(
            opportunity_id=opp.opportunity_id,
            user_id=users[SALES_EXECUTIVE].user_id,
            role=SALES_EXECUTIVE,
        ))
        db.session.commit()
        application.config["A2"] = {"opp": opp.opportunity_id, "users": users}
    return application


def test_lead_approval_is_centralized_and_versioned(app):
    with app.app_context():
        ids = app.config["A2"]
        opp_id = ids["opp"]
        sales = ids["users"][SALES_EXECUTIVE]
        manager = ids["users"][SALES_MANAGER]
        owner = sales
        LifecycleTransitionService.submit_lead(opp_id, 1, sales, SALES_EXECUTIVE)
        opp = Opportunity.query.get(opp_id)
        assert opp.lifecycle_stage == "Lead"
        assert opp.review_status == "Pending Sales Manager Review"
        assert opp.row_version == 2
        LifecycleTransitionService.approve_lead(opp_id, 2, owner.user_id, manager, SALES_MANAGER)
        opp = Opportunity.query.get(opp_id)
        assert (opp.lifecycle_stage, opp.outcome, opp.operational_status) == ("Qualified", "Open", "Active")
        assert opp.row_version == 3


def test_forbidden_edges_are_rejected(app):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        psm = ids["users"][PRE_SALES_MANAGER]
        se = ids["users"][SOLUTION_ENGINEER]
        db.session.add(OpportunityTeam(opportunity_id=opp.opportunity_id, user_id=se.user_id, role=SOLUTION_ENGINEER))
        db.session.commit()
        forbidden = {
            "Lead": ["RFX", "POC", "Negotiations", "Delivery"],
            "Qualified": ["POC", "Negotiations", "Delivery"],
            "RFX": ["Negotiations", "Delivery"],
            "POC": ["RFX", "Delivery"],
            "Negotiations": ["RFX", "POC", "Qualified", "Lead"],
            "Delivery": ["Negotiations", "POC", "RFX", "Qualified", "Lead"],
        }
        # Use direct state setup for graph testing; this does not call a mutation API.
        for current, targets in forbidden.items():
            opp.lifecycle_stage = current
            opp.outcome = "Open"
            opp.operational_status = "Active"
            opp.review_status = "Approved"
            db.session.commit()
            for target in targets:
                opp = Opportunity.query.get(opp.opportunity_id)
                actor = se if current != "Lead" else psm
                role = SOLUTION_ENGINEER if actor is se else PRE_SALES_MANAGER
                with pytest.raises(TransitionInvalid):
                    LifecycleTransitionService.transition(opp.opportunity_id, target, opp.row_version, actor, role)


def test_allowed_graph_with_domain_hooks(app):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        psm = ids["users"][PRE_SALES_MANAGER]
        db.session.add(OpportunityTeam(opportunity_id=opp.opportunity_id, user_id=ids["users"][SOLUTION_ENGINEER].user_id, role=SOLUTION_ENGINEER))
        db.session.commit()
        LifecycleTransitionService.register_precondition("RFX", "POC", lambda opportunity: None)
        LifecycleTransitionService.register_precondition("POC", "Negotiations", lambda opportunity: None)
        try:
            opp.lifecycle_stage = "Qualified"
            opp.review_status = "Approved"
            db.session.commit()
            for target in ["RFX", "POC", "Negotiations", "Delivery"]:
                opp = Opportunity.query.get(opp.opportunity_id)
                actor = psm
                LifecycleTransitionService.transition(opp.opportunity_id, target, opp.row_version, actor, PRE_SALES_MANAGER)
            opp = Opportunity.query.get(opp.opportunity_id)
            assert (opp.lifecycle_stage, opp.outcome, opp.operational_status) == ("Delivery", "Closed Won", "Closed")
        finally:
            LifecycleTransitionService.clear_precondition("RFX", "POC")
            LifecycleTransitionService.clear_precondition("POC", "Negotiations")


def test_closed_state_is_terminal(app):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        psm = ids["users"][PRE_SALES_MANAGER]
        opp.lifecycle_stage = "POC"
        opp.review_status = "Approved"
        db.session.commit()
        LifecycleTransitionService.close_lost(opp.opportunity_id, opp.row_version, "Competitor", None, psm, PRE_SALES_MANAGER)
        opp = Opportunity.query.get(opp.opportunity_id)
        assert opp.outcome == "Closed Lost"
        assert opp.operational_status == "Closed"
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.transition(opp.opportunity_id, "Negotiations", opp.row_version, psm, PRE_SALES_MANAGER)
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.set_operational_status(opp.opportunity_id, "Active", opp.row_version, psm, PRE_SALES_MANAGER)


def test_closed_lost_other_requires_explanation(app):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        manager = ids["users"][SALES_MANAGER]
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.close_lost(opp.opportunity_id, opp.row_version, "Other", None, manager, SALES_MANAGER)
        opp = Opportunity.query.get(opp.opportunity_id)
        assert opp.outcome == "Open"


def test_active_role_not_union_of_roles(app):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        user = ids["users"][SALES_EXECUTIVE]
        user.roles.append(UserRole(role=SOLUTION_ENGINEER))
        db.session.add(OpportunityTeam(opportunity_id=opp.opportunity_id, user_id=user.user_id, role=SOLUTION_ENGINEER))
        opp.lifecycle_stage = "Qualified"
        opp.review_status = "Approved"
        db.session.commit()
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.transition(opp.opportunity_id, "RFX", opp.row_version, user, SALES_EXECUTIVE)


def test_stale_version_is_rejected(app):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        psm = ids["users"][PRE_SALES_MANAGER]
        opp.lifecycle_stage = "Qualified"
        opp.review_status = "Approved"
        db.session.commit()
        expected = opp.row_version
        LifecycleTransitionService.set_operational_status(opp.opportunity_id, "Stalled", expected, psm, PRE_SALES_MANAGER)
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.set_operational_status(opp.opportunity_id, "Active", expected, psm, PRE_SALES_MANAGER)


def test_transition_rolls_back_when_audit_write_fails(app, monkeypatch):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        psm = ids["users"][PRE_SALES_MANAGER]
        opp.lifecycle_stage = "Qualified"
        opp.review_status = "Approved"
        db.session.commit()
        original_version = opp.row_version
        def fail_audit(*args, **kwargs):
            raise RuntimeError("audit unavailable")
        monkeypatch.setattr("app.services.lifecycle_transition_service.ActivityService.log", fail_audit)
        with pytest.raises(RuntimeError):
            LifecycleTransitionService.transition(opp.opportunity_id, "RFX", original_version, psm, PRE_SALES_MANAGER)
        db.session.rollback()
        opp = Opportunity.query.get(opp.opportunity_id)
        assert opp.lifecycle_stage == "Qualified"
        assert opp.row_version == original_version


def test_stage_authorization_uses_active_role(app):
    with app.app_context():
        ids = app.config["A2"]
        opp = Opportunity.query.get(ids["opp"])
        opp.lifecycle_stage = "Qualified"
        opp.review_status = "Approved"
        db.session.commit()
        se = ids["users"][SOLUTION_ENGINEER]
        db.session.add(OpportunityTeam(opportunity_id=opp.opportunity_id, user_id=se.user_id, role=SOLUTION_ENGINEER))
        db.session.commit()
        allowed = {PRE_SALES_MANAGER, SOLUTION_ENGINEER, LEADERSHIP}
        for role in [ADMIN, SALES_EXECUTIVE, SALES_MANAGER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST]:
            actor = ids["users"][role]
            with pytest.raises(AuthorizationDenied):
                LifecycleTransitionService.transition(opp.opportunity_id, "RFX", opp.row_version, actor, role)
        # No mutation was made by denied calls; authorized active roles can proceed.
        psm = ids["users"][PRE_SALES_MANAGER]
        LifecycleTransitionService.transition(opp.opportunity_id, "RFX", opp.row_version, psm, PRE_SALES_MANAGER)
        assert Opportunity.query.get(opp.opportunity_id).lifecycle_stage == "RFX"


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="PostgreSQL integration environment not configured")
def test_postgresql_concurrency_contract(tmp_path):
    """Two independent PostgreSQL sessions must produce one success and one 409-equivalent conflict."""
    import threading

    url = os.environ["TEST_POSTGRES_URL"]
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": url})
    with application.app_context():
        db.drop_all()
        db.create_all()
        account = Account(account_name="A2 PG Account")
        db.session.add(account)
        db.session.flush()
        psm = User(full_name="PG PSM", email="pg_psm_a2@test", password_hash=hash_password("Password123!"), status="APPROVED", active=True)
        psm.roles.append(UserRole(role=PRE_SALES_MANAGER))
        db.session.add(psm)
        db.session.flush()
        opp = Opportunity(account_id=account.account_id, created_by=psm.user_id, stage_id=1, opportunity_name="A2 PG", lifecycle_stage="Qualified", outcome="Open", operational_status="Active", review_status="Approved", row_version=1, status="Active", is_active=True)
        db.session.add(opp)
        db.session.commit()
        opp_id = opp.opportunity_id

    barrier = threading.Barrier(2)
    results = []

    def worker():
        local_app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": url})
        with local_app.app_context():
            local_opp = Opportunity.query.get(opp_id)
            barrier.wait()
            try:
                LifecycleTransitionService.transition(opp_id, "RFX", 1, User.query.get(psm.user_id), PRE_SALES_MANAGER)
                results.append("success")
            except TransitionConflict:
                results.append("conflict")
            finally:
                db.session.remove()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert sorted(results) == ["conflict", "success"]
