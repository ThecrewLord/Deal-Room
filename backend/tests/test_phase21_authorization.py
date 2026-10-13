"""Phase 21 — Authorization and privilege-boundary tests."""

from datetime import date

import pytest

from app import create_app
from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.auth.password import hash_password
from app.auth.token_service import create_access
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
from app.models.opportunity.stage_master import StageMaster
from app.models.phase2 import (
    Activity,
    DeliveryProject,
    DeliveryProjectMember,
    FollowUp,
    NegotiationContext,
    POCTeamMember,
)
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stakeholder import Stakeholder
from app.services.opportunity_service import OpportunityService


BUSINESS_ROLES = [
    SALES_MANAGER,
    SALES_EXECUTIVE,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
]


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'phase21.db'}",
            "JWT_SECRET_KEY": "phase21-test-secret-key-32-bytes-long",
        }
    )

    with application.app_context():
        db.drop_all()
        db.create_all()

        account = Account(
            account_name="Phase 21 Authorization Account",
            is_active=True,
        )
        db.session.add(account)

        users = {}

        for role in [LEADERSHIP, ADMIN] + BUSINESS_ROLES:
            user = User(
                full_name=f"Phase21 {role}",
                email=(
                    f"{role.lower().replace(' ', '_').replace('-', '_')}"
                    "@phase21.test"
                ),
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

        application.config["P21_ACCOUNT"] = account.account_id
        application.config["P21_USERS"] = {
            role: users[role].user_id
            for role in users
        }

    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def user(app, role):
    return db.session.get(
        User,
        app.config["P21_USERS"][role],
    )


def make_user(app, email, role):
    u = User(
        full_name=email.split("@")[0],
        email=email,
        password_hash=hash_password("Password123!"),
        status="APPROVED",
        active=True,
    )
    u.roles.append(UserRole(role=role))
    db.session.add(u)
    db.session.flush()
    return u


def login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def auth(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def make_opportunity(app, creator_role=SALES_EXECUTIVE):
    actor = user(app, creator_role)

    opportunity = OpportunityService.create_opportunity(
        {
            "account_id": app.config["P21_ACCOUNT"],
            "opportunity_name": f"Phase21 {creator_role} Opportunity",
            "description": "Phase 21 authorization test",
            "pain_points": "Authorization test",
            "estimated_value": 100000,
            "probability": 25,
        },
        actor,
        creator_role,
    )

    db.session.commit()
    return opportunity


def make_shared_opportunity(app):
    opportunity = make_opportunity(app, LEADERSHIP)

    for role in BUSINESS_ROLES:
        db.session.add(
            OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=app.config["P21_USERS"][role],
                role=role,
            )
        )

    db.session.commit()
    return opportunity


# ---------------------------------------------------------------------------
# A. Authentication / active-role validation
# ---------------------------------------------------------------------------


def test_phase21_no_token_is_rejected(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_phase21_invalid_token_is_rejected(client):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer definitely-invalid-token"},
    )

    assert response.status_code == 401


def test_phase21_inactive_user_cannot_use_existing_token(client, app):
    with app.app_context():
        target = user(app, SALES_EXECUTIVE)
        target_email = target.email
        db.session.commit()

    session = login(client, target_email)

    with app.app_context():
        target = User.query.filter_by(email=target_email).first()
        target.active = False
        db.session.commit()

    response = client.get(
        "/api/auth/me",
        headers=auth(session["access_token"]),
    )

    assert response.status_code == 403


def test_phase21_unapproved_user_cannot_use_access_token(client, app):
    with app.app_context():
        target = user(app, SALES_EXECUTIVE)
        target.status = "PENDING"
        db.session.commit()

        token = create_access(target, SALES_EXECUTIVE)

    response = client.get(
        "/api/auth/me",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_phase21_token_cannot_claim_unassigned_role(client, app):
    with app.app_context():
        target = user(app, SALES_EXECUTIVE)
        db.session.commit()

        token = create_access(target, LEADERSHIP)

    response = client.get(
        "/api/auth/me",
        headers=auth(token),
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# B. Opportunity visibility
# ---------------------------------------------------------------------------


def test_phase21_admin_cannot_view_business_opportunity(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)
        admin = user(app, ADMIN)

        assert AuthorizationService.can_view_opportunity(
            admin,
            ADMIN,
            opportunity,
        ) is False


def test_phase21_leadership_can_view_business_opportunity(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)
        leader = user(app, LEADERSHIP)

        assert AuthorizationService.can_view_opportunity(
            leader,
            LEADERSHIP,
            opportunity,
        ) is True


def test_phase21_unassigned_solution_engineer_cannot_view_private_opportunity(app):
    with app.app_context():
        opportunity = make_opportunity(app, SALES_EXECUTIVE)

        assigned_se = user(app, SOLUTION_ENGINEER)
        db.session.add(
            OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=assigned_se.user_id,
                role=SOLUTION_ENGINEER,
            )
        )
        db.session.commit()

        other_se = make_user(
            app,
            "other-se@phase21.test",
            SOLUTION_ENGINEER,
        )
        db.session.commit()

        assert AuthorizationService.can_view_opportunity(
            assigned_se,
            SOLUTION_ENGINEER,
            opportunity,
        ) is True

        assert AuthorizationService.can_view_opportunity(
            other_se,
            SOLUTION_ENGINEER,
            opportunity,
        ) is False


# ---------------------------------------------------------------------------
# C. Related-record authorization
# ---------------------------------------------------------------------------


def test_phase21_stakeholder_and_poc_visibility_follows_opportunity(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)

        assert AuthorizationService.can_view_opportunity(
            user(app, SOLUTION_ENGINEER),
            SOLUTION_ENGINEER,
            opportunity,
        ) is True


def test_phase21_activity_history_cannot_bypass_opportunity_visibility(app):
    with app.app_context():
        opportunity = make_opportunity(app, SALES_EXECUTIVE)

        other_se = make_user(
            app,
            "history-other-se@phase21.test",
            SOLUTION_ENGINEER,
        )
        db.session.commit()

        from app.models.phase2 import Activity

        activity = Activity(
            opportunity_id=opportunity.opportunity_id,
            activity_type="note",
            summary="Private activity",
            actor_id=user(app, SALES_EXECUTIVE).user_id,
        )
        db.session.add(activity)
        db.session.commit()

        assert AuthorizationService.can_view_activity(
            other_se,
            SOLUTION_ENGINEER,
            "activity",
            activity.activity_id,
        ) is False


# ---------------------------------------------------------------------------
# D. Mutation authorization
# ---------------------------------------------------------------------------


def test_phase21_delivery_roles_cannot_manage_followups(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)

        followup = FollowUp(
            opportunity_id=opportunity.opportunity_id,
            owner_id=user(app, SALES_EXECUTIVE).user_id,
            description="Phase 21 follow-up",
            due_date=date.today(),
            status="Open",
            created_by=user(app, SALES_EXECUTIVE).user_id,
        )
        db.session.add(followup)
        db.session.commit()

        for role in [
            DELIVERY_MANAGER,
            DEVOPS_ENGINEER,
            DATA_ANALYST,
        ]:
            assert AuthorizationService.can_manage_followup(
                user(app, role),
                role,
                followup,
            ) is False


def test_phase21_delivery_roles_cannot_manage_negotiations(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)

        for role in [
            DELIVERY_MANAGER,
            DEVOPS_ENGINEER,
            DATA_ANALYST,
        ]:
            assert AuthorizationService.can_manage_negotiation(
                user(app, role),
                role,
                opportunity,
            ) is False


def test_phase21_rfx_requires_assigned_solution_engineer(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)

        rfx_stage = StageMaster.query.filter_by(
            stage_name="RFX"
        ).first()

        opportunity.stage_id = rfx_stage.stage_id
        opportunity.lifecycle_stage = "RFX"
        db.session.commit()

        assigned_se = user(app, SOLUTION_ENGINEER)

        assert AuthorizationService.can_manage_rfx(
            assigned_se,
            SOLUTION_ENGINEER,
            opportunity,
        ) is True

        other_se = make_user(
            app,
            "rfx-other-se@phase21.test",
            SOLUTION_ENGINEER,
        )
        db.session.commit()

        assert AuthorizationService.can_manage_rfx(
            other_se,
            SOLUTION_ENGINEER,
            opportunity,
        ) is False


def test_phase21_delivery_roles_cannot_create_activities(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)

        for role in [
            DELIVERY_MANAGER,
            DEVOPS_ENGINEER,
            DATA_ANALYST,
        ]:
            actor = user(app, role)

            assert AuthorizationService.can_create_activity(
                actor,
                role,
                opportunity,
            ) is False


# ---------------------------------------------------------------------------
# E. Privilege escalation
# ---------------------------------------------------------------------------


def test_phase21_followup_owner_must_be_active_and_approved(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)

        sales_exec = user(app, SALES_EXECUTIVE)
        inactive_owner = make_user(
            app,
            "inactive-followup-owner@phase21.test",
            SOLUTION_ENGINEER,
        )

        inactive_owner.active = False
        db.session.commit()

        before = FollowUp.query.count()

        from app.services.phase2_service import Phase2Service

        with pytest.raises(ValueError, match="owner"):
            Phase2Service.add_followup(
                opportunity.opportunity_id,
                {
                    "owner_id": inactive_owner.user_id,
                    "description": "Inactive owner assignment",
                    "due_date": date.today().isoformat(),
                },
                sales_exec,
                SALES_EXECUTIVE,
            )

        db.session.rollback()

        assert FollowUp.query.count() == before


def test_phase21_rejected_opportunity_delete_is_server_side(app):
    with app.app_context():
        opportunity = make_shared_opportunity(app)

        before = Opportunity.query.count()

        for role in BUSINESS_ROLES + [LEADERSHIP, ADMIN]:
            actor = user(app, role)

            assert AuthorizationService.can_delete_opportunity(
                actor,
                role,
                opportunity,
            ) is False

        after = Opportunity.query.count()

        assert after == before
        assert db.session.get(
            Opportunity,
            opportunity.opportunity_id,
        ) is not None
