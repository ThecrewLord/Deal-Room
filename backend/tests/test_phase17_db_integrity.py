import pytest
from datetime import date

from sqlalchemy.exc import IntegrityError

from app import create_app
from app.auth.password import hash_password
from app.constants.roles import (
    SALES_EXECUTIVE,
    SOLUTION_ENGINEER,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
)
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stage_master import StageMaster
from app.models.phase2 import (
    POCTeamMember,
    DeliveryProject,
    DeliveryProjectMember,
    Activity,
    FollowUp,
)
from app.services.opportunity_service import OpportunityService
from app.services.phase2_service import Phase2Service


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'phase17.db'}",
        "JWT_SECRET_KEY": "phase17-test-secret",
    })

    with application.app_context():
        db.drop_all()
        db.create_all()
        db.session.execute(db.text("PRAGMA foreign_keys=ON"))

        account = Account(
            account_name="Phase 17 Integrity Account",
            is_active=True,
        )
        db.session.add(account)

        users = {}
        for role in [
            SALES_EXECUTIVE,
            SOLUTION_ENGINEER,
            DELIVERY_MANAGER,
            DEVOPS_ENGINEER,
            DATA_ANALYST,
        ]:
            user = User(
                full_name=f"Phase17 {role}",
                email=f"{role.lower().replace(' ', '_')}@phase17.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            user.roles.append(UserRole(role=role))
            db.session.add(user)
            users[role] = user

        db.session.flush()

        stages = {}
        for order, name in enumerate(
            ("Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"),
            1,
        ):
            stage = StageMaster(
                stage_name=name,
                display_order=order,
                requires_poc=(name == "POC"),
                is_closed=False,
                is_won=False,
            )
            db.session.add(stage)
            stages[name] = stage

        db.session.flush()
        db.session.commit()

        application.config["P17_ACCOUNT"] = account.account_id
        application.config["P17_USERS"] = {
            role: user.user_id
            for role, user in users.items()
        }
        application.config["P17_STAGES"] = {
            name: stage.stage_id
            for name, stage in stages.items()
        }

    return application


def user(app, role):
    return db.session.get(
        User,
        app.config["P17_USERS"][role],
    )


def make_opportunity(app):
    actor = user(app, SALES_EXECUTIVE)

    opportunity = OpportunityService.create_opportunity(
        {
            "account_id": app.config["P17_ACCOUNT"],
            "opportunity_name": "Phase 17 Integrity Opportunity",
            "description": "Integrity test opportunity",
            "pain_points": "Integrity test pain",
            "estimated_value": 100000,
            "probability": 25,
        },
        actor,
        SALES_EXECUTIVE,
    )

    db.session.commit()
    return opportunity


def test_phase17_invalid_opportunity_outcome_is_rejected(app):
    with app.app_context():
        opportunity = make_opportunity(app)

        opportunity.outcome = "Invalid Outcome"

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_invalid_followup_status_is_rejected(app):
    with app.app_context():
        opportunity = make_opportunity(app)
        actor = user(app, SALES_EXECUTIVE)

        followup = FollowUp(
            opportunity_id=opportunity.opportunity_id,
            owner_id=actor.user_id,
            description="Integrity test follow-up",
            due_date=date.today(),
            status="Invalid Status",
            created_by=actor.user_id,
        )

        db.session.add(followup)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_invalid_activity_type_is_rejected(app):
    with app.app_context():
        opportunity = make_opportunity(app)
        actor = user(app, SALES_EXECUTIVE)

        activity = Activity(
            opportunity_id=opportunity.opportunity_id,
            activity_type="email",
            summary="Integrity test activity",
            actor_id=actor.user_id,
        )

        db.session.add(activity)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_invalid_poc_team_role_is_rejected(app):
    with app.app_context():
        opportunity = make_opportunity(app)
        poc = POCTracker(
            opportunity_id=opportunity.opportunity_id,
            poc_name="Phase 17 Integrity POC",
            target_date=date.today(),
            status="Draft",
        )
        db.session.add(poc)
        db.session.flush()

        actor = user(app, SALES_EXECUTIVE)

        member = POCTeamMember(
            poc_id=poc.poc_id,
            user_id=actor.user_id,
            role="Invalid Role",
            assigned_by=actor.user_id,
        )

        db.session.add(member)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_invalid_delivery_project_status_is_rejected(app):
    with app.app_context():
        opportunity = make_opportunity(app)
        manager = user(app, DELIVERY_MANAGER)

        project = DeliveryProject(
            opportunity_id=opportunity.opportunity_id,
            account_id=opportunity.account_id,
            manager_id=manager.user_id,
            status="Invalid Status",
        )

        db.session.add(project)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_invalid_foreign_key_is_rejected(app):
    with app.app_context():
        actor = user(app, SALES_EXECUTIVE)

        activity = Activity(
            opportunity_id=999999,
            activity_type="note",
            summary="Invalid opportunity reference",
            actor_id=actor.user_id,
        )

        db.session.add(activity)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_missing_required_field_is_rejected(app):
    with app.app_context():
        actor = user(app, SALES_EXECUTIVE)

        activity = Activity(
            opportunity_id=999999,
            activity_type="note",
            summary=None,
            actor_id=actor.user_id,
        )

        db.session.add(activity)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_duplicate_opportunity_team_relationship_is_rejected(app):
    with app.app_context():
        opportunity = make_opportunity(app)
        actor = user(app, SOLUTION_ENGINEER)

        first = OpportunityTeam(
            opportunity_id=opportunity.opportunity_id,
            user_id=actor.user_id,
            role=SOLUTION_ENGINEER,
        )
        second = OpportunityTeam(
            opportunity_id=opportunity.opportunity_id,
            user_id=actor.user_id,
            role=SOLUTION_ENGINEER,
        )

        db.session.add_all([first, second])

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


def test_phase17_delivery_project_uses_opportunity_account(app):
    with app.app_context():
        opportunity = make_opportunity(app)

        opportunity.outcome = "Closed Won"
        opportunity.operational_status = "Closed"
        db.session.commit()

        manager = user(app, DELIVERY_MANAGER)

        project = DeliveryProject(
            opportunity_id=opportunity.opportunity_id,
            account_id=opportunity.account_id,
            manager_id=manager.user_id,
            status="Active",
            row_version=1,
        )

        db.session.add(project)
        db.session.commit()

        assert project.opportunity_id == opportunity.opportunity_id
        assert project.account_id == opportunity.account_id
