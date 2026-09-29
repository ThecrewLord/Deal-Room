"""Phase 19 — Role and authorization matrix tests."""

from datetime import date

import pytest

from app import create_app
from app.auth.authorization import AuthorizationService
from app.auth.password import hash_password
from app.constants.roles import (
    ADMIN,
    DATA_ANALYST,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
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
from app.models.opportunity.poc_tracker import POCTracker
from app.models.phase2 import FollowUp
from app.models.opportunity.stage_master import StageMaster
from app.services.opportunity_service import OpportunityService


BUSINESS_ROLES = [
    SALES_EXECUTIVE,
    SALES_MANAGER,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
]


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'phase19.db'}",
        "JWT_SECRET_KEY": "phase19-test-secret",
    })

    with application.app_context():
        db.drop_all()
        db.create_all()

        account = Account(
            account_name="Phase 19 Test Account",
            is_active=True,
        )
        db.session.add(account)

        users = {}

        for role in [LEADERSHIP, ADMIN] + BUSINESS_ROLES:
            user = User(
                full_name=f"Phase19 {role}",
                email=f"{role.lower().replace(' ', '_').replace('-', '_')}@phase19.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            user.roles.append(UserRole(role=role))
            db.session.add(user)
            users[role] = user

        db.session.flush()

        for order, name in enumerate(
            ("Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"),
            1,
        ):
            db.session.add(
                StageMaster(
                    stage_name=name,
                    display_order=order,
                    requires_poc=(name == "POC"),
                    is_closed=False,
                    is_won=False,
                )
            )

        db.session.commit()

        application.config["P19_ACCOUNT"] = account.account_id
        application.config["P19_USERS"] = {
            role: users[role].user_id
            for role in users
        }

    return application


def user(app, role):
    return db.session.get(
        User,
        app.config["P19_USERS"][role],
    )


def make_lead(app, role=SALES_EXECUTIVE):
    actor = user(app, role)

    opp = OpportunityService.create_opportunity(
        {
            "account_id": app.config["P19_ACCOUNT"],
            "opportunity_name": f"Phase19 {role} Lead",
            "description": "Phase 19 authorization test",
            "pain_points": "Phase 19 test pain",
            "estimated_value": 100000,
            "probability": 25,
        },
        actor,
        role,
    )

    db.session.commit()
    return opp.opportunity_id


def test_phase19_admin_is_not_a_business_role(app):
    with app.app_context():
        actor = user(app, ADMIN)

        assert AuthorizationService.can_create_opportunity(
            actor,
            ADMIN,
        ) is False

        assert AuthorizationService.can_delete_opportunity(
            actor,
            ADMIN,
            None,
        ) is False


def test_phase19_all_business_roles_can_create_opportunity(app):
    with app.app_context():
        for role in BUSINESS_ROLES:
            actor = user(app, role)

            assert AuthorizationService.can_create_opportunity(
                actor,
                role,
            ) is True


def test_phase19_no_business_role_can_delete_opportunity(app):
    with app.app_context():
        for role in BUSINESS_ROLES + [LEADERSHIP]:
            actor = user(app, role)

            assert AuthorizationService.can_delete_opportunity(
                actor,
                role,
                None,
            ) is False



def make_shared_opportunity(app):
    """Create one opportunity visible to the roles needed by matrix tests."""
    opp_id = make_lead(app, LEADERSHIP)
    opp = db.session.get(Opportunity, opp_id)

    for role in BUSINESS_ROLES:
        db.session.add(
            OpportunityTeam(
                opportunity_id=opp.opportunity_id,
                user_id=app.config["P19_USERS"][role],
                role=role,
            )
        )

    db.session.commit()
    return opp


def test_phase19_delivery_roles_cannot_manage_followups(app):
    with app.app_context():
        opp = make_shared_opportunity(app)

        followup = FollowUp(
            opportunity_id=opp.opportunity_id,
            owner_id=app.config["P19_USERS"][SALES_EXECUTIVE],
            description="Phase 19 follow-up",
            due_date=date.today(),
            status="Open",
            created_by=app.config["P19_USERS"][SALES_EXECUTIVE],
        )
        db.session.add(followup)
        db.session.commit()

        for role in [DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST]:
            actor = user(app, role)

            assert AuthorizationService.can_manage_followup(
                actor,
                role,
                followup,
            ) is False


def test_phase19_delivery_roles_cannot_manage_negotiations(app):
    with app.app_context():
        opp = make_shared_opportunity(app)

        for role in [DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST]:
            actor = user(app, role)

            assert AuthorizationService.can_manage_negotiation(
                actor,
                role,
                opp,
            ) is False


def test_phase19_only_assigned_solution_engineer_can_change_technical_stage(app):
    with app.app_context():
        opp = make_shared_opportunity(app)

        se = user(app, SOLUTION_ENGINEER)

        for role in BUSINESS_ROLES:
            actor = user(app, role)

            expected = role == SOLUTION_ENGINEER

            assert AuthorizationService.can_change_technical_stage(
                actor,
                role,
                opp,
            ) is expected


def test_phase19_only_assigned_solution_engineer_can_request_poc(app):
    with app.app_context():
        opp = make_shared_opportunity(app)

        poc_stage = StageMaster.query.filter_by(
            stage_name="POC"
        ).first()

        assert poc_stage is not None

        opp.stage_id = poc_stage.stage_id
        opp.lifecycle_stage = "POC"
        db.session.commit()

        for role in BUSINESS_ROLES:
            actor = user(app, role)

            expected = role == SOLUTION_ENGINEER

            assert AuthorizationService.can_request_poc(
                actor,
                role,
                opp,
            ) is expected


def test_phase19_only_leadership_can_mutate_oem_master(app):
    with app.app_context():
        for role in [LEADERSHIP, ADMIN] + BUSINESS_ROLES:
            actor = user(app, role)

            expected = role == LEADERSHIP

            assert AuthorizationService.can_mutate_oem_master(
                actor,
                role,
            ) is expected


def test_phase19_opportunity_visibility_admin_blocked_leadership_allowed(app):
    with app.app_context():
        opp = make_shared_opportunity(app)

        leadership = user(app, LEADERSHIP)
        admin = user(app, ADMIN)

        assert AuthorizationService.can_view_opportunity(
            leadership,
            LEADERSHIP,
            opp,
        ) is True

        assert AuthorizationService.can_view_opportunity(
            admin,
            ADMIN,
            opp,
        ) is False
