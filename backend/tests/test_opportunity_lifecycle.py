"""Phase 1 V2 certification suite.

This suite intentionally tests the frozen V2 core rather than obsolete A1-A5
V1/V2 transition behavior. SQLite is used for fast unit/integration coverage;
PostgreSQL migration/concurrency verification is performed separately in CI or
against the project PostgreSQL environment.
"""
import pytest
from decimal import Decimal
from datetime import date

from app import create_app
from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.auth.password import hash_password
from app.auth.token_service import create_access
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
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stage_master import StageMaster
from app.models.phase2 import RFXContext
from app.models.opportunity.stakeholder import Stakeholder
from app.schemas.opportunity_schema import OpportunityCreateSchema, OpportunityReviewSchema
from app.services.lifecycle_transition_service import LifecycleTransitionService, TransitionConflict, TransitionInvalid
from app.services.opportunity_service import OpportunityService
from app.services.opportunity_value_service import OpportunityValueService


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'phase1.db'}",
        "JWT_SECRET_KEY": "phase1-test-secret",
    })
    with application.app_context():
        db.drop_all()
        db.create_all()
        account = Account(account_name="Phase 1 Canonical Account", is_active=True)
        db.session.add(account)
        for role in [LEADERSHIP, ADMIN, SALES_MANAGER, SALES_EXECUTIVE, PRE_SALES_MANAGER,
                     SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST]:
            user = User(
                full_name=f"Phase1 {role}",
                email=f"{role.lower().replace(' ', '_').replace('-', '_')}@phase1.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED", active=True,
            )
            user.roles.append(UserRole(role=role))
            db.session.add(user)
        db.session.flush()
        for order, name in enumerate(("Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"), 1):
            db.session.add(StageMaster(stage_name=name, display_order=order, requires_poc=(name == "POC"), is_closed=False, is_won=False))
        db.session.commit()
        application.config["P1_ACCOUNT"] = account.account_id
        application.config["P1_USERS"] = {u.role_names()[0]: u.user_id for u in User.query.all()}
    return application


def user(app, role):
    return User.query.get(app.config["P1_USERS"][role])


def make_lead(app, role=SALES_EXECUTIVE, name=None):
    with app.app_context():
        actor = user(app, role)
        opp = OpportunityService.create_opportunity({
            "account_id": app.config["P1_ACCOUNT"],
            "opportunity_name": name or f"P1 {role} Lead",
            "description": "Customer description",
            "pain_points": "Customer pain",
            "estimated_value": 100000,
            "probability": 25,
        }, actor, role)
        db.session.add(Stakeholder(opportunity_id=opp.opportunity_id, stakeholder_name="Decision Maker"))
        db.session.commit()
        return opp.opportunity_id


def submit(app, opportunity_id, role=SALES_EXECUTIVE):
    with app.app_context():
        actor = user(app, role)
        opp = Opportunity.query.get(opportunity_id)
        return LifecycleTransitionService.submit_lead(opportunity_id, opp.row_version, actor, role)


def approve(app, opportunity_id):
    with app.app_context():
        manager = user(app, SALES_MANAGER)
        sales_exec = user(app, SALES_EXECUTIVE)
        opp = Opportunity.query.get(opportunity_id)
        return LifecycleTransitionService.approve_lead(opportunity_id, opp.row_version, sales_exec.user_id, manager, SALES_MANAGER)


def test_lifecycle_stages_are_correct(app):
    with app.app_context():
        rows = StageMaster.query.order_by(StageMaster.display_order).all()
        assert [(r.display_order, r.stage_name, r.is_closed, r.is_won) for r in rows] == [
            (1, "Lead", False, False), (2, "Qualified", False, False),
            (3, "RFX", False, False), (4, "POC", False, False),
            (5, "Negotiations", False, False), (6, "Delivery", False, False),
        ]


def test_eligible_roles_can_create_and_submit(app):
    roles = [LEADERSHIP, SALES_MANAGER, SALES_EXECUTIVE, PRE_SALES_MANAGER,
             SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST]
    for i, role in enumerate(roles):
        oid = make_lead(app, role, f"Eligible {i}")
        with app.app_context():
            actor = user(app, role)
            opp = Opportunity.query.get(oid)
            LifecycleTransitionService.submit_lead(oid, opp.row_version, actor, role)
            opp = Opportunity.query.get(oid)
            assert (opp.lifecycle_stage, opp.outcome, opp.operational_status, opp.review_status, opp.row_version) == (
                "Lead", "Open", "Active", "Pending Sales Manager Review", 2
            )
    with app.app_context():
        assert AuthorizationService.can_create_opportunity(user(app, ADMIN), ADMIN) is False


def test_deal_finder_is_immutable(app):
    schema = OpportunityCreateSchema()
    with pytest.raises(Exception):
        schema.load({"account_id": 1, "opportunity_name": "Injected", "estimated_value": 1, "deal_finder_id": 999})
    oid = make_lead(app)
    with app.app_context():
        opp = Opportunity.query.get(oid)
        original = opp.created_by
        assert original == user(app, SALES_EXECUTIVE).user_id
        with pytest.raises(ValueError):
            OpportunityService.update_opportunity(oid, {"deal_finder_id": 999, "expected_version": opp.row_version}, user(app, SALES_EXECUTIVE), SALES_EXECUTIVE)
        assert Opportunity.query.get(oid).created_by == original


def test_lead_submission_requires_required_fields(app):
    with app.app_context():
        actor = user(app, SALES_EXECUTIVE)
        opp = OpportunityService.create_opportunity({
            "account_id": app.config["P1_ACCOUNT"], "opportunity_name": "Incomplete Lead", "estimated_value": 10,
        }, actor, SALES_EXECUTIVE)
        db.session.commit()
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.submit_lead(opp.opportunity_id, 1, actor, SALES_EXECUTIVE)
        opp.description = "Description"; opp.pain_points = "Pain"; db.session.add(opp); db.session.commit()
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.submit_lead(opp.opportunity_id, opp.row_version, actor, SALES_EXECUTIVE)


def test_sales_manager_review_allows_only_valid_decisions(app):
    schema = OpportunityReviewSchema()
    for decision in ("APPROVE", "CLOSE_WON", "CLOSE_LOST"):
        assert schema.load({"decision": decision, "expected_version": 1})["decision"] == decision
    with pytest.raises(Exception):
        schema.load({"decision": "REJECT", "expected_version": 1})


def test_sales_manager_can_self_review_and_assign(app):
    oid = make_lead(app, SALES_MANAGER, "Manager Self Review")
    with app.app_context():
        manager = user(app, SALES_MANAGER)
        owner = user(app, SALES_EXECUTIVE)
        LifecycleTransitionService.submit_lead(oid, 2 - 1, manager, SALES_MANAGER)
        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.approve_lead(oid, opp.row_version, owner.user_id, manager, SALES_MANAGER)
        opp = Opportunity.query.get(oid)
        assert opp.created_by == manager.user_id
        assert opp.sales_owner_id == owner.user_id
        assert opp.lifecycle_stage == "Qualified"


def test_lifecycle_progression_and_delivery_gate(app):
    oid = make_lead(app)
    submit(app, oid); approve(app, oid)
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        db.session.add(OpportunityTeam(
            opportunity_id=oid, user_id=se.user_id, role=SOLUTION_ENGINEER
        ))
        db.session.commit()
        opp = Opportunity.query.get(oid)

        LifecycleTransitionService.transition(oid, "RFX", opp.row_version, se, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)

        db.session.add(RFXContext(
            opportunity_id=oid,
            drive_link="https://drive.google.com/test-rfx-context",
            created_by=psm.user_id,
        ))
        db.session.commit()
        opp = Opportunity.query.get(oid)

        LifecycleTransitionService.transition(oid, "POC", opp.row_version, se, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        assert opp.lifecycle_stage == "POC"

        poc = POCTracker(
            opportunity_id=oid,
            poc_name="Certification POC",
            target_date=date.today(),
            status="Completed",
            outcome="Success",
            result_view_link="https://drive.google.com/poc-result",
            requested_by=psm.user_id,
            submitted_by=psm.user_id,
        )
        db.session.add(poc)
        db.session.commit()
        opp = Opportunity.query.get(oid)

        LifecycleTransitionService.transition(oid, "Negotiations", opp.row_version, se, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        assert opp.lifecycle_stage == "Negotiations"

        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.transition(oid, "Delivery", opp.row_version, se, SOLUTION_ENGINEER)
        assert Opportunity.query.get(oid).outcome == "Open"


def test_closed_won_from_open_stages_snapshots_revenue(app):
    # Qualified onward is closed by Pre-Sales Manager; Lead is closed by Sales Manager.
    lead_oid = make_lead(app, SALES_EXECUTIVE, "Lead Won")
    submit(app, lead_oid)
    with app.app_context():
        manager = user(app, SALES_MANAGER); opp = Opportunity.query.get(lead_oid)
        LifecycleTransitionService.close_won(lead_oid, opp.row_version, manager, SALES_MANAGER)
        won = Opportunity.query.get(lead_oid)
        assert (won.lifecycle_stage, won.outcome, won.operational_status, won.final_revenue) == ("Lead", "Closed Won", "Closed", Decimal("100000.00"))

    for stage in ("Qualified", "RFX", "POC", "Negotiations"):
        oid = make_lead(app, SALES_EXECUTIVE, f"{stage} Won")
        submit(app, oid); approve(app, oid)
        with app.app_context():
            psm = user(app, PRE_SALES_MANAGER)
            se = user(app, SOLUTION_ENGINEER)
            opp = Opportunity.query.get(oid)
            db.session.add(OpportunityTeam(
                opportunity_id=oid, user_id=se.user_id, role=SOLUTION_ENGINEER
            ))
            db.session.commit()
            opp = Opportunity.query.get(oid)
            stage_order = ["Qualified", "RFX", "POC", "Negotiations"]
            target_index = stage_order.index(stage)
            for target in stage_order[1:target_index + 1]:
                if target == "POC":
                    db.session.add(RFXContext(
                        opportunity_id=oid,
                        drive_link="https://drive.google.com/test-rfx-context",
                        created_by=psm.user_id,
                    ))
                    db.session.commit()
                    opp = Opportunity.query.get(oid)
                LifecycleTransitionService.transition(oid, target, opp.row_version, se, SOLUTION_ENGINEER)
                opp = Opportunity.query.get(oid)
                if target == "POC":
                    poc = POCTracker(
                        opportunity_id=oid,
                        poc_name="Certification POC",
                                                            target_date=date.today(),
                                    status="Completed",
                        outcome="Success",
                                    result_view_link="https://drive.google.com/poc-result",
                        requested_by=psm.user_id,
                        submitted_by=psm.user_id,
                    )
                    db.session.add(poc)
                    db.session.commit()
                    opp = Opportunity.query.get(oid)
            LifecycleTransitionService.close_won(oid, opp.row_version, psm, PRE_SALES_MANAGER)
            won = Opportunity.query.get(oid)
            expected_stage = "Delivery" if stage == "Negotiations" else stage
            assert won.lifecycle_stage == expected_stage
            assert won.outcome == "Closed Won" and won.operational_status == "Closed"
            assert won.final_revenue == Decimal("100000.00")


def test_closed_lost_requires_reason_details(app):
    oid = make_lead(app)
    submit(app, oid)
    with app.app_context():
        manager = user(app, SALES_MANAGER); opp = Opportunity.query.get(oid)
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.close_lost(oid, opp.row_version, "Other", None, manager, SALES_MANAGER)
        LifecycleTransitionService.close_lost(oid, opp.row_version, "Other", "Budget was cancelled", manager, SALES_MANAGER)
        lost = Opportunity.query.get(oid)
        assert (lost.outcome, lost.operational_status, lost.lost_reason, lost.lost_explanation) == ("Closed Lost", "Closed", "Other", "Budget was cancelled")


def test_value_changes_are_authorized_historic_and_concurrent(app):
    oid = make_lead(app)
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER); se = user(app, SALES_EXECUTIVE)
        opp = Opportunity.query.get(oid)
        OpportunityValueService.change_value(oid, 125000, "Commercial revision", opp.row_version, psm, PRE_SALES_MANAGER)
        opp = Opportunity.query.get(oid)
        assert opp.estimated_value == Decimal("125000.00") and opp.row_version == 2
        with pytest.raises(AuthorizationDenied):
            OpportunityValueService.change_value(oid, 130000, "Unauthorized", opp.row_version, se, SALES_EXECUTIVE)
        with pytest.raises(TransitionConflict):
            OpportunityValueService.change_value(oid, 130000, "Stale", 1, psm, PRE_SALES_MANAGER)


def test_closed_opportunity_is_locked(app):
    oid = make_lead(app); submit(app, oid)
    with app.app_context():
        manager = user(app, SALES_MANAGER); opp = Opportunity.query.get(oid)
        LifecycleTransitionService.close_won(oid, opp.row_version, manager, SALES_MANAGER)
        closed = Opportunity.query.get(oid)
        with pytest.raises(TransitionConflict):
            OpportunityValueService.change_value(oid, 200000, "Too late", closed.row_version, manager, SALES_MANAGER)
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.close_lost(oid, closed.row_version, "Competitor", None, manager, SALES_MANAGER)


def test_active_role_isolation(app):
    with app.app_context():
        dual = user(app, SOLUTION_ENGINEER)
        dual.roles.append(UserRole(role=SALES_EXECUTIVE)); db.session.commit()
        oid = make_lead(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        assert AuthorizationService.can_view_opportunity(dual, SOLUTION_ENGINEER, opp)
        assert AuthorizationService.can_view_opportunity(dual, SALES_EXECUTIVE, opp) is False
        # Active Sales Executive cannot inherit Solution Engineer stage authority.
        assert AuthorizationService.can_change_lifecycle_stage(dual, SALES_EXECUTIVE, opp, "Qualified") is False


def test_leadership_sees_business_data_admin_does_not(app):
    oid = make_lead(app)
    with app.app_context():
        opp = Opportunity.query.get(oid)
        assert AuthorizationService.can_view_opportunity(user(app, LEADERSHIP), LEADERSHIP, opp)
        assert not AuthorizationService.can_view_opportunity(user(app, ADMIN), ADMIN, opp)


def _qualify_and_assign_se(app, name="Group1"):
    oid = make_lead(app, SALES_EXECUTIVE, name)
    submit(app, oid)
    approve(app, oid)
    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        db.session.add(OpportunityTeam(
            opportunity_id=oid, user_id=se.user_id, role=SOLUTION_ENGINEER
        ))
        db.session.commit()
        return oid


def test_group1_qualified_to_rfx_requires_assigned_se(app):
    oid = _qualify_and_assign_se(app, "Assigned SE RFX")
    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.transition(oid, "RFX", opp.row_version, se, SOLUTION_ENGINEER)
        assert Opportunity.query.get(oid).lifecycle_stage == "RFX"


def test_group1_unassigned_and_sales_exec_cannot_enter_rfx(app):
    oid = _qualify_and_assign_se(app, "Unauthorized RFX")
    with app.app_context():
        assigned_se = user(app, SOLUTION_ENGINEER)
        other_se = User(
            full_name="Unrelated SE",
            email="unrelated-se@phase1.test",
            password_hash=hash_password("Password123!"),
            status="APPROVED", active=True,
        )
        other_se.roles.append(UserRole(role=SOLUTION_ENGINEER))
        db.session.add(other_se)
        db.session.commit()
        opp = Opportunity.query.get(oid)

        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.transition(
                oid, "RFX", opp.row_version, other_se, SOLUTION_ENGINEER
            )

        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.transition(
                oid, "RFX", opp.row_version,
                user(app, SALES_EXECUTIVE), SALES_EXECUTIVE
            )

        assert Opportunity.query.get(oid).lifecycle_stage == "Qualified"


def test_group1_psm_does_not_gain_technical_transition_authority(app):
    oid = _qualify_and_assign_se(app, "PSM Cannot Transition")
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        opp = Opportunity.query.get(oid)
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.transition(
                oid, "RFX", opp.row_version, psm, PRE_SALES_MANAGER
            )


def test_group1_rfx_to_poc_requires_drive_context_and_assigned_se(app):
    oid = _qualify_and_assign_se(app, "RFX POC")
    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.transition(oid, "RFX", opp.row_version, se, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)

        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.transition(
                oid, "POC", opp.row_version, se, SOLUTION_ENGINEER
            )

        db.session.add(RFXContext(
            opportunity_id=oid,
            drive_link="https://drive.google.com/test-rfx-context",
            created_by=se.user_id,
        ))
        db.session.commit()
        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.transition(oid, "POC", opp.row_version, se, SOLUTION_ENGINEER)
        assert Opportunity.query.get(oid).lifecycle_stage == "POC"


def test_group1_poc_to_negotiations_is_explicit_and_assigned_se_only(app):
    oid = _qualify_and_assign_se(app, "POC Negotiations")
    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        sales_exec = user(app, SALES_EXECUTIVE)
        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.transition(oid, "RFX", opp.row_version, se, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        db.session.add(RFXContext(
            opportunity_id=oid,
            drive_link="https://drive.google.com/test-rfx-context",
            created_by=se.user_id,
        ))
        db.session.commit()
        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.transition(oid, "POC", opp.row_version, se, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)

        # A POC artifact does not automatically move the lifecycle. The
        # explicit SE action is the only thing that enters Negotiations.
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.transition(
                oid, "Negotiations", opp.row_version, sales_exec, SALES_EXECUTIVE
            )

        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.transition(
            oid, "Negotiations", opp.row_version, se, SOLUTION_ENGINEER
        )
        assert Opportunity.query.get(oid).lifecycle_stage == "Negotiations"


@pytest.mark.parametrize("current,target", [
    ("Lead", "RFX"),
    ("Lead", "POC"),
    ("Qualified", "POC"),
    ("Qualified", "Negotiations"),
    ("RFX", "Negotiations"),
    ("POC", "Delivery"),
])
def test_group1_stage_skipping_rejected(app, current, target):
    oid = make_lead(app, SALES_EXECUTIVE, f"Skip {current} {target}")
    if current != "Lead":
        submit(app, oid)
        approve(app, oid)

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        db.session.add(OpportunityTeam(
            opportunity_id=oid, user_id=se.user_id, role=SOLUTION_ENGINEER
        ))
        db.session.commit()
        opp = Opportunity.query.get(oid)

        if current == "Lead":
            # Lead cannot be advanced directly by the technical transition path.
            with pytest.raises(AuthorizationDenied):
                LifecycleTransitionService.transition(
                    oid, target, opp.row_version, se, SOLUTION_ENGINEER
                )
            return

        if current in {"RFX", "POC"}:
            LifecycleTransitionService.transition(
                oid, "RFX", opp.row_version, se, SOLUTION_ENGINEER
            )
            opp = Opportunity.query.get(oid)

        if current == "POC":
            db.session.add(RFXContext(
                opportunity_id=oid,
                drive_link="https://drive.google.com/test-rfx-context",
                created_by=se.user_id,
            ))
            db.session.commit()
            opp = Opportunity.query.get(oid)
            LifecycleTransitionService.transition(
                oid, "POC", opp.row_version, se, SOLUTION_ENGINEER
            )
            opp = Opportunity.query.get(oid)

        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.transition(
                oid, target, opp.row_version, se, SOLUTION_ENGINEER
            )


def test_group1_stale_version_returns_conflict(app):
    oid = _qualify_and_assign_se(app, "Stale Version")
    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        stale = opp.row_version
        LifecycleTransitionService.transition(
            oid, "RFX", stale, se, SOLUTION_ENGINEER
        )
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.transition(
                oid, "POC", stale, se, SOLUTION_ENGINEER
            )


def test_group1_closed_opportunity_rejects_lifecycle_mutation(app):
    oid = _qualify_and_assign_se(app, "Closed Lifecycle Lock")
    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        psm = user(app, PRE_SALES_MANAGER)
        opp = Opportunity.query.get(oid)
        LifecycleTransitionService.close_won(
            oid, opp.row_version, psm, PRE_SALES_MANAGER
        )
        closed = Opportunity.query.get(oid)

        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.transition(
                oid, "RFX", closed.row_version, se, SOLUTION_ENGINEER
            )

        assert (
            Opportunity.query.get(oid).outcome,
            Opportunity.query.get(oid).operational_status,
            Opportunity.query.get(oid).lifecycle_stage,
        ) == ("Closed Won", "Closed", "Qualified")


def test_group1_generic_update_schema_cannot_accept_lifecycle_state(app):
    from marshmallow import ValidationError
    from app.schemas.opportunity_schema import OpportunityUpdateSchema

    with pytest.raises(ValidationError):
        OpportunityUpdateSchema().load({
            "lifecycle_stage": "Negotiations",
            "expected_version": 1,
        })

def test_group1_direct_api_enforces_transition_authorization_and_stale_version(app):
    oid = _qualify_and_assign_se(app, "Direct API Security")
    client = app.test_client()

    with app.app_context():
        sales_exec = user(app, SALES_EXECUTIVE)
        assigned_se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        version = opp.row_version

        # Direct API call must not allow Sales Executive to bypass lifecycle
        # authorization merely because the endpoint exists.
        sales_exec_token = create_access(sales_exec, SALES_EXECUTIVE)
        response = client.post(
            f"/api/opportunities/{oid}/advance-to-rfx",
            json={"expected_version": version},
            headers={"Authorization": f"Bearer {sales_exec_token}"},
        )
        assert response.status_code == 403

        # Assigned SE can use the domain action through the API.
        se_token = create_access(assigned_se, SOLUTION_ENGINEER)
        response = client.post(
            f"/api/opportunities/{oid}/advance-to-rfx",
            json={"expected_version": version},
            headers={"Authorization": f"Bearer {se_token}"},
        )
        assert response.status_code == 200

        # Reusing the previous version through the API must be a 409.
        response = client.post(
            f"/api/opportunities/{oid}/advance-to-poc",
            json={"expected_version": version},
            headers={"Authorization": f"Bearer {se_token}"},
        )
        assert response.status_code == 409


def test_group1_direct_api_rejects_client_controlled_lifecycle_fields(app):
    oid = make_lead(app, SALES_EXECUTIVE, "Direct API State Injection")
    client = app.test_client()

    with app.app_context():
        actor = user(app, SALES_EXECUTIVE)
        opp = Opportunity.query.get(oid)
        token = create_access(actor, SALES_EXECUTIVE)
        response = client.put(
            f"/api/opportunities/{oid}",
            json={
                "lifecycle_stage": "Negotiations",
                "expected_version": opp.row_version,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert Opportunity.query.get(oid).lifecycle_stage == "Lead"



def _qualified_without_se(app, name="Group2"):
    oid = make_lead(app, SALES_EXECUTIVE, name)
    submit(app, oid)
    approve(app, oid)
    return oid


def test_group2_psm_can_assign_valid_solution_engineer(app):
    oid = _qualified_without_se(app, "G2 Valid Assignment")
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        old_version = opp.row_version

        updated = OpportunityService.finalize_pre_sales_assignment(
            oid, se.user_id, old_version, psm, PRE_SALES_MANAGER
        )

        assert updated.lifecycle_stage == "Qualified"
        assert updated.row_version == old_version + 1
        team = OpportunityTeam.query.filter_by(
            opportunity_id=oid, user_id=se.user_id, role=SOLUTION_ENGINEER
        ).one()
        assert team.user_id == se.user_id
        assert Opportunity.query.get(oid).created_by == user(app, SALES_EXECUTIVE).user_id
        assert Opportunity.query.get(oid).sales_owner_id == user(app, SALES_EXECUTIVE).user_id


@pytest.mark.parametrize("role", [
    SALES_MANAGER, SALES_EXECUTIVE, SOLUTION_ENGINEER,
    DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST,
])
def test_group2_non_psm_cannot_assign_solution_engineer(app, role):
    oid = _qualified_without_se(app, f"G2 Unauthorized {role}")
    with app.app_context():
        actor = user(app, role)
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        with pytest.raises(AuthorizationDenied):
            OpportunityService.finalize_pre_sales_assignment(
                oid, se.user_id, opp.row_version, actor, role
            )
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 0


def test_group2_candidate_must_really_be_solution_engineer(app):
    oid = _qualified_without_se(app, "G2 Candidate Role Validation")
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        invalid = user(app, SALES_EXECUTIVE)
        opp = Opportunity.query.get(oid)
        with pytest.raises(ValueError, match="eligible Solution Engineer"):
            OpportunityService.finalize_pre_sales_assignment(
                oid, invalid.user_id, opp.row_version, psm, PRE_SALES_MANAGER
            )
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 0


def test_group2_inactive_candidate_rejected(app):
    oid = _qualified_without_se(app, "G2 Inactive Candidate")
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        se.active = False
        db.session.commit()
        opp = Opportunity.query.get(oid)
        with pytest.raises(ValueError, match="eligible Solution Engineer"):
            OpportunityService.finalize_pre_sales_assignment(
                oid, se.user_id, opp.row_version, psm, PRE_SALES_MANAGER
            )


@pytest.mark.parametrize("stage", ["Lead", "RFX", "POC", "Negotiations", "Delivery"])
def test_group2_assignment_only_allowed_at_qualified(app, stage):
    oid = _qualified_without_se(app, f"G2 Wrong Stage {stage}")
    with app.app_context():
        opp = Opportunity.query.get(oid)
        opp.lifecycle_stage = stage
        db.session.commit()
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        with pytest.raises(AuthorizationDenied):
            OpportunityService.finalize_pre_sales_assignment(
                oid, se.user_id, opp.row_version, psm, PRE_SALES_MANAGER
            )
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 0


@pytest.mark.parametrize("outcome", ["Closed Won", "Closed Lost"])
def test_group2_closed_opportunity_cannot_receive_se(app, outcome):
    oid = _qualified_without_se(app, f"G2 Closed {outcome}")
    with app.app_context():
        opp = Opportunity.query.get(oid)
        opp.outcome = outcome
        opp.operational_status = "Closed"
        db.session.commit()
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        with pytest.raises(AuthorizationDenied):
            OpportunityService.finalize_pre_sales_assignment(
                oid, se.user_id, opp.row_version, psm, PRE_SALES_MANAGER
            )
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 0


def test_group2_duplicate_assignment_is_rejected(app):
    oid = _qualified_without_se(app, "G2 Duplicate Assignment")
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        OpportunityService.finalize_pre_sales_assignment(
            oid, se.user_id, opp.row_version, psm, PRE_SALES_MANAGER
        )
        opp = Opportunity.query.get(oid)
        assert AuthorizationService.can_finalize_pre_sales_assignment(
            psm, PRE_SALES_MANAGER, opp
        ) is False
        with pytest.raises(AuthorizationDenied):
            OpportunityService.finalize_pre_sales_assignment(
                oid, se.user_id, opp.row_version, psm, PRE_SALES_MANAGER
            )
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 1


def test_group2_stale_row_version_returns_conflict(app):
    oid = _qualified_without_se(app, "G2 Stale Version")
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        stale = opp.row_version - 1
        with pytest.raises(RuntimeError, match="stale"):
            OpportunityService.finalize_pre_sales_assignment(
                oid, se.user_id, stale, psm, PRE_SALES_MANAGER
            )
        assert Opportunity.query.get(oid).row_version == opp.row_version
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 0


def test_group2_direct_api_rejects_non_psm_and_accepts_psm(app):
    oid = _qualified_without_se(app, "G2 Direct API")
    client = app.test_client()
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        sales_manager = user(app, SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        version = opp.row_version

        sm_response = client.post(
            f"/api/opportunities/{oid}/finalize-pre-sales-assignment",
            json={"solution_engineer_id": se.user_id, "row_version": version},
            headers={"Authorization": f"Bearer {create_access(sales_manager, SALES_MANAGER)}"},
        )
        assert sm_response.status_code == 403

        psm_response = client.post(
            f"/api/opportunities/{oid}/finalize-pre-sales-assignment",
            json={"solution_engineer_id": se.user_id, "row_version": version},
            headers={"Authorization": f"Bearer {create_access(psm, PRE_SALES_MANAGER)}"},
        )
        assert psm_response.status_code == 200

        # A stale client must be rejected before any assignment is created.
        stale_oid = _qualified_without_se(app, "G2 Direct API Stale")
        stale_opp = Opportunity.query.get(stale_oid)
        stale_response = client.post(
            f"/api/opportunities/{stale_oid}/finalize-pre-sales-assignment",
            json={"solution_engineer_id": se.user_id, "row_version": stale_opp.row_version - 1},
            headers={"Authorization": f"Bearer {create_access(psm, PRE_SALES_MANAGER)}"},
        )
        assert stale_response.status_code == 409
        assert OpportunityTeam.query.filter_by(
            opportunity_id=stale_oid, role=SOLUTION_ENGINEER
        ).count() == 0


def test_group2_assignment_request_cannot_control_unrelated_fields(app):
    oid = _qualified_without_se(app, "G2 Field Protection")
    client = app.test_client()
    with app.app_context():
        psm = user(app, PRE_SALES_MANAGER)
        se = user(app, SOLUTION_ENGINEER)
        opp = Opportunity.query.get(oid)
        original_creator = opp.created_by
        original_stage = opp.lifecycle_stage
        original_outcome = opp.outcome
        original_status = opp.operational_status

        response = client.post(
            f"/api/opportunities/{oid}/finalize-pre-sales-assignment",
            json={
                "solution_engineer_id": se.user_id,
                "row_version": opp.row_version,
                "lifecycle_stage": "Negotiations",
                "outcome": "Closed Won",
                "operational_status": "Closed",
                "created_by": 999999,
            },
            headers={"Authorization": f"Bearer {create_access(psm, PRE_SALES_MANAGER)}"},
        )
        assert response.status_code == 400

        fresh = Opportunity.query.get(oid)
        assert fresh.created_by == original_creator
        assert fresh.lifecycle_stage == original_stage
        assert fresh.outcome == original_outcome
        assert fresh.operational_status == original_status
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 0


def test_group2_direct_api_rejects_unauthenticated_and_role_spoofing(app):
    oid = _qualified_without_se(app, "G2 API Role Spoofing")
    client = app.test_client()
    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)
        psm = user(app, PRE_SALES_MANAGER)
        opp = Opportunity.query.get(oid)

        unauthenticated = client.post(
            f"/api/opportunities/{oid}/finalize-pre-sales-assignment",
            json={"solution_engineer_id": se.user_id, "row_version": opp.row_version},
        )
        assert unauthenticated.status_code in (401, 403)

        spoofed = client.post(
            f"/api/opportunities/{oid}/finalize-pre-sales-assignment",
            json={
                "solution_engineer_id": se.user_id,
                "row_version": opp.row_version,
                "role": SOLUTION_ENGINEER,
            },
            headers={"Authorization": f"Bearer {create_access(psm, PRE_SALES_MANAGER)}"},
        )
        assert spoofed.status_code == 400
        assert OpportunityTeam.query.filter_by(
            opportunity_id=oid, role=SOLUTION_ENGINEER
        ).count() == 0
