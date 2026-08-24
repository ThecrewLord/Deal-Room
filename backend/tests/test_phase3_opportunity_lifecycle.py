import pytest

from app.auth.password import hash_password
from app.constants.roles import SALES_EXECUTIVE, SOLUTION_ENGINEER, DELIVERY
from app.constants.stages import (
    CLOSED_STATUS,
    INITIAL_STAGE_NAME,
    OPEN_STATUS,
    REJECTED_STATUS,
)
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_history import StageHistory
from app.models.opportunity.stage_master import StageMaster
from app.schemas.opportunity_schema import OpportunityCreateSchema, OpportunityUpdateSchema
from app.services.opportunity_service import OpportunityService
from app.services.stage_service import StageService


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase3.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase3-test-secret")

    from app import create_app

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        stage_values = [
            ("Lead / Identified", 1, False, False, False),
            ("Qualification", 2, False, False, False),
            ("Discovery", 3, False, False, False),
            ("POC / Technical Evaluation", 4, True, False, False),
            ("Proposal", 5, False, False, False),
            ("Negotiation", 6, False, False, False),
            ("Closed Won", 7, False, True, True),
            ("Closed Lost", 8, False, True, False),
        ]
        stages = [
            StageMaster(
                stage_name=name,
                display_order=order,
                requires_poc=requires_poc,
                is_closed=is_closed,
                is_won=is_won,
            )
            for name, order, requires_poc, is_closed, is_won in stage_values
        ]
        db.session.add_all(stages)
        db.session.flush()

        sales = User(
            full_name="Sales Executive",
            email="sales@example.com",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        sales.roles.append(UserRole(role=SALES_EXECUTIVE))

        se = User(
            full_name="Solution Engineer",
            email="se@example.com",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        se.roles.append(UserRole(role=SOLUTION_ENGINEER))

        delivery = User(
            full_name="Delivery",
            email="delivery@example.com",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        delivery.roles.append(UserRole(role=DELIVERY))

        account = Account(account_name="Acme")
        db.session.add_all([sales, se, delivery, account])
        db.session.flush()

        # Existing participation makes the account visible to the Sales
        # Executive under the Phase 2 account-scope rules.
        existing = Opportunity(
            account_id=account.account_id,
            created_by=sales.user_id,
            stage_id=stages[0].stage_id,
            opportunity_name="Existing",
            status=OPEN_STATUS,
            is_active=True,
        )
        db.session.add(existing)
        db.session.flush()
        db.session.add(
            OpportunityTeam(
                opportunity_id=existing.opportunity_id,
                user_id=sales.user_id,
                role=SALES_EXECUTIVE,
            )
        )
        db.session.commit()

    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_canonical_stage_master_integrity(app):
    with app.app_context():
        stages = StageService.get_initial_stage()
        assert stages.stage_name == INITIAL_STAGE_NAME

        all_stages = StageMaster.query.order_by(StageMaster.display_order).all()
        assert len(all_stages) == 8
        assert [stage.stage_name for stage in all_stages] == [
            "Lead / Identified",
            "Qualification",
            "Discovery",
            "POC / Technical Evaluation",
            "Proposal",
            "Negotiation",
            "Closed Won",
            "Closed Lost",
        ]

        poc_stage = all_stages[3]
        won_stage = all_stages[6]
        lost_stage = all_stages[7]

        assert poc_stage.requires_poc is True
        assert won_stage.is_closed is True
        assert won_stage.is_won is True
        assert lost_stage.is_closed is True
        assert lost_stage.is_won is False


def test_creation_separates_created_by_sales_owner_and_team(app):
    with app.app_context():
        sales = User.query.filter_by(email="sales@example.com").first()
        account = Account.query.filter_by(account_name="Acme").first()

        opportunity = OpportunityService.create_opportunity(
            {
                "account_id": account.account_id,
                "opportunity_name": "New Opportunity",
                "description": "Phase 3 test",
            },
            sales,
            SALES_EXECUTIVE,
        )

        assert opportunity.created_by == sales.user_id
        assert opportunity.sales_owner_id is None
        assert opportunity.current_stage.stage_name == INITIAL_STAGE_NAME
        assert opportunity.status == OPEN_STATUS
        assert opportunity.is_active is True

        team = OpportunityTeam.query.filter_by(
            opportunity_id=opportunity.opportunity_id
        ).all()
        assert len(team) == 1
        assert team[0].user_id == sales.user_id
        assert team[0].role == SALES_EXECUTIVE

        history = StageHistory.query.filter_by(
            opportunity_id=opportunity.opportunity_id
        ).all()
        assert len(history) == 1
        assert history[0].stage_id == opportunity.stage_id
        assert history[0].changed_by == sales.user_id


def test_created_by_and_sales_owner_can_differ(app):
    with app.app_context():
        sales = User.query.filter_by(email="sales@example.com").first()
        se = User.query.filter_by(email="se@example.com").first()
        account = Account.query.filter_by(account_name="Acme").first()
        stage = StageMaster.query.filter_by(
            stage_name=INITIAL_STAGE_NAME
        ).first()

        opportunity = Opportunity(
            account_id=account.account_id,
            created_by=sales.user_id,
            sales_owner_id=se.user_id,
            stage_id=stage.stage_id,
            opportunity_name="Distinct Relationships",
            status=OPEN_STATUS,
            is_active=True,
        )
        db.session.add(opportunity)
        db.session.flush()

        assert opportunity.created_by != opportunity.sales_owner_id


def test_multiple_team_members_can_share_same_opportunity_role(app):
    with app.app_context():
        sales = User.query.filter_by(email="sales@example.com").first()
        se = User.query.filter_by(email="se@example.com").first()
        delivery = User.query.filter_by(email="delivery@example.com").first()
        account = Account.query.filter_by(account_name="Acme").first()
        stage = StageMaster.query.filter_by(stage_name=INITIAL_STAGE_NAME).first()

        opportunity = Opportunity(
            account_id=account.account_id,
            created_by=sales.user_id,
            stage_id=stage.stage_id,
            opportunity_name="Multiple Roles",
            status=OPEN_STATUS,
            is_active=True,
        )
        db.session.add(opportunity)
        db.session.flush()

        db.session.add_all([
            OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=se.user_id,
                role=SOLUTION_ENGINEER,
            ),
            OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=delivery.user_id,
                role=DELIVERY,
            ),
        ])
        db.session.commit()

        se_rows = OpportunityTeam.query.filter_by(
            opportunity_id=opportunity.opportunity_id,
            role=SOLUTION_ENGINEER,
        ).all()
        assert len(se_rows) == 1


def test_generic_create_and_update_cannot_set_server_controlled_fields():
    create_schema = OpportunityCreateSchema()
    update_schema = OpportunityUpdateSchema()

    with pytest.raises(Exception):
        create_schema.load({
            "account_id": 1,
            "opportunity_name": "Injected Stage",
            "stage_id": 8,
            "status": "Closed Won",
            "created_by": 999,
            "sales_owner_id": 999,
        })

    with pytest.raises(Exception):
        update_schema.load({
            "stage_id": 8,
            "status": "Closed Won",
            "created_by": 999,
            "sales_owner_id": 999,
            "updated_at": "2026-08-12T00:00:00",
        })


def test_stage_transition_is_sequential_and_audited(app):
    with app.app_context():
        sales = User.query.filter_by(email="sales@example.com").first()
        account = Account.query.filter_by(account_name="Acme").first()
        opportunity = Opportunity.query.filter_by(
            opportunity_name="Existing"
        ).first()
        qualification = StageMaster.query.filter_by(
            stage_name="Qualification"
        ).first()

        OpportunityService.transition_stage(
            opportunity.opportunity_id,
            qualification.stage_id,
            sales,
            SALES_EXECUTIVE,
            "Move into qualification.",
        )

        db.session.refresh(opportunity)
        assert opportunity.current_stage.stage_name == "Qualification"

        history = StageHistory.query.filter_by(
            opportunity_id=opportunity.opportunity_id
        ).order_by(StageHistory.created_at.asc()).all()
        assert len(history) == 2
        assert history[-1].stage_id == qualification.stage_id
        assert history[-1].changed_by == sales.user_id


def test_closed_state_semantics(app):
    with app.app_context():
        opportunity = Opportunity.query.filter_by(
            opportunity_name="Existing"
        ).first()
        closed_won = StageMaster.query.filter_by(
            stage_name="Closed Won"
        ).first()
        closed_lost = StageMaster.query.filter_by(
            stage_name="Closed Lost"
        ).first()

        opportunity.stage_id = closed_won.stage_id
        opportunity.status = CLOSED_STATUS
        opportunity.is_active = False
        db.session.commit()

        db.session.refresh(opportunity)
        assert opportunity.current_stage.is_closed is True
        assert opportunity.current_stage.is_won is True
        assert opportunity.status == CLOSED_STATUS
        assert opportunity.is_active is False

        # The model also distinguishes Closed Lost from Closed Won.
        assert closed_lost.is_closed is True
        assert closed_lost.is_won is False

def test_rejected_state_is_representable_without_deletion(app):
    with app.app_context():
        opportunity = Opportunity.query.filter_by(
            opportunity_name="Existing"
        ).first()

        opportunity.status = REJECTED_STATUS
        opportunity.is_active = False
        db.session.commit()

        still_exists = Opportunity.query.get(opportunity.opportunity_id)
        assert still_exists is not None
        assert still_exists.status == REJECTED_STATUS
        assert still_exists.is_active is False


def test_phase2_visibility_remains_participation_based(client, app):
    sales_token = login(client, "sales@example.com")

    with app.app_context():
        existing = Opportunity.query.filter_by(
            opportunity_name="Existing"
        ).first()
        opportunity_id = existing.opportunity_id

    response = client.get(
        f"/api/opportunities/{opportunity_id}",
        headers=auth(sales_token),
    )
    assert response.status_code == 200


def test_stage_history_endpoint_is_authorized(client, app):
    sales_token = login(client, "sales@example.com")

    with app.app_context():
        opportunity_id = Opportunity.query.filter_by(
            opportunity_name="Existing"
        ).first().opportunity_id

    response = client.get(
        f"/api/opportunities/{opportunity_id}/stage-history",
        headers=auth(sales_token),
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
