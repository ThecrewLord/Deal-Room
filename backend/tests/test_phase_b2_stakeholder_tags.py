import pytest

from app.auth.password import hash_password
from app.constants.roles import SALES_EXECUTIVE
from app.constants.stages import OPEN_STATUS
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.stage_master import StageMaster


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase_b2.db"

    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite:///{db_path}",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "phase-b2-test-secret",
    )

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

        sales.roles.append(
            UserRole(role=SALES_EXECUTIVE)
        )

        account = Account(
            account_name="Acme Corporation",
        )

        db.session.add_all([
            sales,
            account,
        ])

        db.session.flush()

        opportunity = Opportunity(
            account_id=account.account_id,
            created_by=sales.user_id,
            stage_id=stages[0].stage_id,
            opportunity_name="B2 Opportunity",
            status=OPEN_STATUS,
            is_active=True,
        )

        opportunity_two = Opportunity(
            account_id=account.account_id,
            created_by=sales.user_id,
            stage_id=stages[0].stage_id,
            opportunity_name="B2 Opportunity Two",
            status=OPEN_STATUS,
            is_active=True,
        )

        db.session.add_all([
            opportunity,
            opportunity_two,
        ])

        db.session.flush()

        db.session.add_all([
            OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=sales.user_id,
                role=SALES_EXECUTIVE,
            ),
            OpportunityTeam(
                opportunity_id=opportunity_two.opportunity_id,
                user_id=sales.user_id,
                role=SALES_EXECUTIVE,
            ),
        ])

        db.session.flush()

        stakeholder = Stakeholder(
            opportunity_id=opportunity.opportunity_id,
            stakeholder_name="John Smith",
            designation="CTO",
            email="john@example.com",
            phone="9999999999",
            influence_level="High",
            notes="Primary technical stakeholder",
        )

        stakeholder_two = Stakeholder(
            opportunity_id=opportunity.opportunity_id,
            stakeholder_name="Jane Smith",
            designation="CEO",
            email="jane@example.com",
            phone="8888888888",
            influence_level="High",
            notes="Executive stakeholder",
        )

        stakeholder_three = Stakeholder(
            opportunity_id=opportunity_two.opportunity_id,
            stakeholder_name="Mike Smith",
            designation="Director",
            email="mike@example.com",
            phone="7777777777",
            influence_level="Medium",
            notes="Stakeholder on second opportunity",
        )

        db.session.add_all([
            stakeholder,
            stakeholder_two,
            stakeholder_three,
        ])

        db.session.commit()

        application.config["B2_TEST_STAKEHOLDER_ID"] = (
            stakeholder.stakeholder_id
        )

        application.config["B2_TEST_STAKEHOLDER_TWO_ID"] = (
            stakeholder_two.stakeholder_id
        )

        application.config["B2_TEST_STAKEHOLDER_THREE_ID"] = (
            stakeholder_three.stakeholder_id
        )

        application.config["B2_TEST_OPPORTUNITY_ID"] = (
            opportunity.opportunity_id
        )

        application.config["B2_TEST_OPPORTUNITY_TWO_ID"] = (
            opportunity_two.opportunity_id
        )

    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "sales@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    token = data.get("access_token")

    assert token is not None

    return {
        "Authorization": f"Bearer {token}",
    }


def test_valid_tag_can_be_added(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    response = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Economic Buyer",
        },
        headers=headers,
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["tag"] == "Economic Buyer"
    assert data["stakeholder_id"] == stakeholder_id


def test_multiple_tags_can_exist_on_same_stakeholder(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    first = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Economic Buyer",
        },
        headers=headers,
    )

    second = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Decision Maker",
        },
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        f"/api/stakeholder/{stakeholder_id}/tags",
        headers=headers,
    )

    assert response.status_code == 200

    tags = response.get_json()

    tag_names = {item["tag"] for item in tags}

    assert tag_names == {
        "Economic Buyer",
        "Decision Maker",
    }


def test_duplicate_tag_is_rejected(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    first = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Blocker",
        },
        headers=headers,
    )

    second = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Blocker",
        },
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_tag_is_rejected(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    response = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Invalid Tag",
        },
        headers=headers,
    )

    assert response.status_code == 400


def test_only_one_decision_maker_per_opportunity(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    stakeholder_two_id = app.config[
        "B2_TEST_STAKEHOLDER_TWO_ID"
    ]

    first = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Decision Maker",
        },
        headers=headers,
    )

    second = client.post(
        f"/api/stakeholder/{stakeholder_two_id}/tags",
        json={
            "tag": "Decision Maker",
        },
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_decision_maker_allowed_on_different_opportunity(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    stakeholder_three_id = app.config[
        "B2_TEST_STAKEHOLDER_THREE_ID"
    ]

    first = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Decision Maker",
        },
        headers=headers,
    )

    second = client.post(
        f"/api/stakeholder/{stakeholder_three_id}/tags",
        json={
            "tag": "Decision Maker",
        },
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 201


def test_tag_can_be_removed(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    create_response = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Technical Champion",
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    tag_id = create_response.get_json()[
        "stakeholder_tag_id"
    ]

    delete_response = client.delete(
        f"/api/stakeholder/tags/{tag_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    get_response = client.get(
        f"/api/stakeholder/{stakeholder_id}/tags",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.get_json() == []


def test_decision_maker_lookup(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    opportunity_id = app.config[
        "B2_TEST_OPPORTUNITY_ID"
    ]

    create_response = client.post(
        f"/api/stakeholder/{stakeholder_id}/tags",
        json={
            "tag": "Decision Maker",
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/stakeholder/opportunity/{opportunity_id}/decision-maker",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["tag"] == "Decision Maker"
    assert data["stakeholder_id"] == stakeholder_id
    assert data["opportunity_id"] == opportunity_id


def test_existing_stakeholder_crud_still_works(client, app):
    headers = login(client)

    stakeholder_id = app.config["B2_TEST_STAKEHOLDER_ID"]

    get_response = client.get(
        f"/api/stakeholder/{stakeholder_id}",
        headers=headers,
    )

    assert get_response.status_code == 200

    data = get_response.get_json()

    assert data["stakeholder_id"] == stakeholder_id

    update_response = client.put(
        f"/api/stakeholder/{stakeholder_id}",
        json={
            "designation": "Chief Technology Officer",
        },
        headers=headers,
    )

    assert update_response.status_code == 200

    updated = update_response.get_json()

    assert updated["designation"] == "Chief Technology Officer"
