import pytest
from marshmallow import ValidationError

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
from app.models.opportunity.stakeholder import Stakeholder
from app.schemas.opportunity_schema import OpportunityCreateSchema
from app.services.opportunity_service import OpportunityService
from app.services.lifecycle_transition_service import (
    LifecycleTransitionService, TransitionConflict, TransitionInvalid,
)
from app.auth.authorization import AuthorizationDenied, AuthorizationService


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'a3.db'}")
    monkeypatch.setenv("JWT_SECRET_KEY", "a3-test-secret")
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'a3.db'}",
    })
    with application.app_context():
        db.drop_all()
        db.create_all()
        account = Account(account_name="A3 Canonical Account", is_active=True)
        db.session.add(account)
        db.session.flush()
        users = {}
        for role in [
            LEADERSHIP, ADMIN, SALES_MANAGER, SALES_EXECUTIVE,
            PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER,
            DEVOPS_ENGINEER, DATA_ANALYST,
        ]:
            user = User(
                full_name=role,
                email=f"{role.lower().replace(' ', '_')}@a3.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            user.roles.append(UserRole(role=role))
            db.session.add(user)
            db.session.flush()
            users[role] = user
        application.config["A3"] = {"account": account.account_id, "users": users}
        db.session.commit()
    return application


def make_lead(app, role=SALES_EXECUTIVE, name="A3 Lead"):
    ids = app.config["A3"]
    user = ids["users"][role]
    with app.app_context():
        opportunity = OpportunityService.create_opportunity({
            "account_id": ids["account"],
            "opportunity_name": name,
            "description": "Customer needs a secure sales platform.",
            "pain_points": "Manual opportunity tracking is slow.",
            "estimated_value": 100000,
            "probability": 20,
            "expected_close_date": None,
        }, user, role)
        db.session.add(Stakeholder(
            opportunity_id=opportunity.opportunity_id,
            stakeholder_name="A3 Buyer",
            designation="CIO",
        ))
        db.session.commit()
        return opportunity.opportunity_id


def test_all_approved_active_roles_except_admin_can_create(app):
    for i, role in enumerate([
        LEADERSHIP, SALES_MANAGER, SALES_EXECUTIVE, PRE_SALES_MANAGER,
        SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST,
    ]):
        assert AuthorizationService.can_create_opportunity(
            app.config["A3"]["users"][role], role
        ) is True
    assert AuthorizationService.can_create_opportunity(
        app.config["A3"]["users"][ADMIN], ADMIN
    ) is False


def test_creation_forces_lead_and_records_deal_finder(app):
    opportunity_id = make_lead(app)
    with app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        finder = app.config["A3"]["users"][SALES_EXECUTIVE]
        assert opportunity.created_by == finder.user_id
        assert opportunity.sales_owner_id is None
        assert opportunity.lifecycle_stage == "Lead"
        assert opportunity.outcome == "Open"
        assert opportunity.operational_status == "Active"
        assert opportunity.review_status == "Draft"
        assert opportunity.estimated_value == 100000
        assert opportunity.pain_points


def test_creation_requires_initial_value_and_rejects_client_state_fields():
    schema = OpportunityCreateSchema()
    with pytest.raises(ValidationError):
        schema.load({"account_id": 1, "opportunity_name": "Missing Value"})
    with pytest.raises(ValidationError):
        schema.load({
            "account_id": 1,
            "opportunity_name": "State Injection",
            "estimated_value": 1,
            "lifecycle_stage": "Qualified",
            "deal_finder_id": 999,
        })


def test_admin_cannot_create_even_with_valid_payload(app):
    ids = app.config["A3"]
    with app.app_context(), pytest.raises(AuthorizationDenied):
        OpportunityService.create_opportunity({
            "account_id": ids["account"],
            "opportunity_name": "Admin Attempt",
            "estimated_value": 1,
        }, ids["users"][ADMIN], ADMIN)


def test_submit_requires_description_pain_points_and_stakeholder(app):
    ids = app.config["A3"]
    with app.app_context():
        user = ids["users"][SALES_EXECUTIVE]
        opportunity = OpportunityService.create_opportunity({
            "account_id": ids["account"],
            "opportunity_name": "Validation Lead",
            "estimated_value": 10,
            "description": None,
            "pain_points": None,
        }, user, SALES_EXECUTIVE)
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.submit_lead(opportunity.opportunity_id, 1, user, SALES_EXECUTIVE)
        opportunity.description = "Description"
        opportunity.pain_points = "Pain"
        db.session.commit()
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.submit_lead(opportunity.opportunity_id, opportunity.row_version, user, SALES_EXECUTIVE)
        db.session.add(Stakeholder(opportunity_id=opportunity.opportunity_id, stakeholder_name="Buyer"))
        db.session.commit()
        LifecycleTransitionService.submit_lead(opportunity.opportunity_id, opportunity.row_version, user, SALES_EXECUTIVE)
        opportunity = Opportunity.query.get(opportunity.opportunity_id)
        assert opportunity.lifecycle_stage == "Lead"
        assert opportunity.review_status == "Pending Sales Manager Review"


def test_wrong_active_role_cannot_submit(app):
    opportunity_id = make_lead(app)
    with app.app_context():
        finder = app.config["A3"]["users"][SALES_EXECUTIVE]
        finder.roles.append(UserRole(role=SOLUTION_ENGINEER))
        db.session.commit()
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.submit_lead(opportunity_id, 1, finder, SOLUTION_ENGINEER)


def test_approval_assigns_sales_exec_without_changing_deal_finder(app):
    opportunity_id = make_lead(app)
    with app.app_context():
        finder = app.config["A3"]["users"][SALES_EXECUTIVE]
        manager = app.config["A3"]["users"][SALES_MANAGER]
        owner = app.config["A3"]["users"][SALES_MANAGER]
        # owner must actually be Sales Executive; use finder as valid target.
        LifecycleTransitionService.submit_lead(opportunity_id, 1, finder, SALES_EXECUTIVE)
        OpportunityService.review_opportunity(
            opportunity_id, "APPROVE", finder.user_id, None, 2, manager, SALES_MANAGER,
            editable_fields={"description": "Manager-edited description", "pain_points": "Updated pain"},
        )
        opportunity = Opportunity.query.get(opportunity_id)
        assert opportunity.created_by == finder.user_id
        assert opportunity.sales_owner_id == finder.user_id
        assert opportunity.lifecycle_stage == "Qualified"
        assert opportunity.review_status == "Approved"
        assert opportunity.row_version == 3


def test_sales_manager_creator_can_approve_own_lead(app):
    opportunity_id = make_lead(app, SALES_MANAGER, "Manager Found Lead")
    with app.app_context():
        manager = app.config["A3"]["users"][SALES_MANAGER]
        sales_exec = app.config["A3"]["users"][SALES_EXECUTIVE]
        LifecycleTransitionService.submit_lead(opportunity_id, 1, manager, SALES_MANAGER)
        OpportunityService.review_opportunity(
            opportunity_id, "APPROVE", sales_exec.user_id, None, 2, manager, SALES_MANAGER
        )
        opportunity = Opportunity.query.get(opportunity_id)
        assert opportunity.created_by == manager.user_id
        assert opportunity.sales_owner_id == sales_exec.user_id
        assert opportunity.lifecycle_stage == "Qualified"


def test_reject_is_not_closed_lost_and_is_versioned(app):
    opportunity_id = make_lead(app)
    with app.app_context():
        finder = app.config["A3"]["users"][SALES_EXECUTIVE]
        manager = app.config["A3"]["users"][SALES_MANAGER]
        LifecycleTransitionService.submit_lead(opportunity_id, 1, finder, SALES_EXECUTIVE)
        LifecycleTransitionService.reject_lead(opportunity_id, 2, "Needs more customer detail", manager, SALES_MANAGER)
        opportunity = Opportunity.query.get(opportunity_id)
        assert opportunity.lifecycle_stage == "Lead"
        assert opportunity.outcome == "Open"
        assert opportunity.operational_status == "Active"
        assert opportunity.review_status == "Rejected"
        assert opportunity.row_version == 3


def test_stale_approval_returns_409_conflict_semantics(app):
    opportunity_id = make_lead(app)
    with app.app_context():
        finder = app.config["A3"]["users"][SALES_EXECUTIVE]
        manager = app.config["A3"]["users"][SALES_MANAGER]
        LifecycleTransitionService.submit_lead(opportunity_id, 1, finder, SALES_EXECUTIVE)
        expected = 2
        LifecycleTransitionService.approve_lead(opportunity_id, expected, finder.user_id, manager, SALES_MANAGER)
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.approve_lead(opportunity_id, expected, finder.user_id, manager, SALES_MANAGER)


def test_initial_lead_close_won_and_lost_require_review_and_preserve_finder(app):
    won_id = make_lead(app, SALES_EXECUTIVE, "Won Lead")
    lost_id = make_lead(app, SALES_EXECUTIVE, "Lost Lead")
    with app.app_context():
        finder = app.config["A3"]["users"][SALES_EXECUTIVE]
        manager = app.config["A3"]["users"][SALES_MANAGER]
        LifecycleTransitionService.submit_lead(won_id, 1, finder, SALES_EXECUTIVE)
        LifecycleTransitionService.close_won(won_id, 2, manager, SALES_MANAGER)
        won = Opportunity.query.get(won_id)
        assert (won.lifecycle_stage, won.outcome, won.operational_status) == ("Lead", "Closed Won", "Closed")
        assert won.created_by == finder.user_id

        LifecycleTransitionService.submit_lead(lost_id, 1, finder, SALES_EXECUTIVE)
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.close_lost(lost_id, 2, "Other", None, manager, SALES_MANAGER)
        LifecycleTransitionService.close_lost(lost_id, 2, "Competitor", None, manager, SALES_MANAGER)
        lost = Opportunity.query.get(lost_id)
        assert (lost.lifecycle_stage, lost.outcome, lost.operational_status) == ("Lead", "Closed Lost", "Closed")
        assert lost.created_by == finder.user_id


def test_deal_finder_is_not_an_update_field(app):
    opportunity_id = make_lead(app)
    with app.app_context():
        opportunity = Opportunity.query.get(opportunity_id)
        finder = app.config["A3"]["users"][SALES_EXECUTIVE]
        # The public update schema has no Deal Finder field; even a direct
        # service call cannot mutate it because the allowed field set excludes it.
        original = opportunity.created_by
        with pytest.raises(ValueError):
            OpportunityService.update_opportunity(
                opportunity_id,
                {"deal_finder_id": 999, "expected_version": opportunity.row_version},
                finder,
                SALES_EXECUTIVE,
            )
        opportunity = Opportunity.query.get(opportunity_id)
        assert opportunity.created_by == original


def test_deal_finder_can_add_stakeholder_only_in_editable_lead_review_states(app):
    ids = app.config["A3"]
    with app.app_context():
        finder = ids["users"][SALES_EXECUTIVE]
        opportunity_id = make_lead(app, SALES_EXECUTIVE, "Stakeholder Authorization Lead")
        opportunity = Opportunity.query.get(opportunity_id)

        # make_lead already creates one stakeholder; verify the service permits
        # the Deal Finder to add another while the Lead is still Draft.
        from app.services.stakeholder_service import StakeholderService
        stakeholder = StakeholderService.create_stakeholder({
            "opportunity_id": opportunity_id,
            "stakeholder_name": "Second Buyer",
            "designation": "CFO",
        }, finder, SALES_EXECUTIVE)
        assert stakeholder.opportunity_id == opportunity_id

        # A non-Deal-Finder Sales Executive must not inherit stakeholder-create
        # authority merely from having the Sales Executive role.
        other = User(
            full_name="Other Sales Executive",
            email="other_se@a3.test",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        other.roles.append(UserRole(role=SALES_EXECUTIVE))
        db.session.add(other)
        db.session.commit()
        with pytest.raises(AuthorizationDenied):
            StakeholderService.create_stakeholder({
                "opportunity_id": opportunity_id,
                "stakeholder_name": "Unauthorized Buyer",
            }, other, SALES_EXECUTIVE)

        # Once submitted, the Deal Finder's stakeholder-create window closes.
        LifecycleTransitionService.submit_lead(opportunity_id, opportunity.row_version, finder, SALES_EXECUTIVE)
        opportunity = Opportunity.query.get(opportunity_id)
        with pytest.raises(AuthorizationDenied):
            StakeholderService.create_stakeholder({
                "opportunity_id": opportunity_id,
                "stakeholder_name": "Late Buyer",
            }, finder, SALES_EXECUTIVE)
