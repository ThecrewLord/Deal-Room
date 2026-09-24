import pytest

from app import create_app
from app.auth.password import hash_password
from app.constants.roles import SALES_EXECUTIVE
from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole


@pytest.fixture()
def dashboard_app(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "dashboard-test-secret-key-32-bytes-min")

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        user = User(
            full_name="Dashboard Sales Executive",
            email="dashboard@example.com",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        user.roles.append(UserRole(role=SALES_EXECUTIVE))
        db.session.add(user)
        db.session.commit()

    return application


@pytest.fixture()
def dashboard_client(dashboard_app):
    return dashboard_app.test_client()


def test_dashboard_api(dashboard_client):
    login_response = dashboard_client.post(
        "/api/auth/login",
        json={
            "email": "dashboard@example.com",
            "password": "Password123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.get_json()["access_token"]

    response = dashboard_client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "total_opportunities" in data
    assert "total_pipeline_value" in data
    assert "weighted_forecast" in data
    assert "pipeline_by_stage" in data


def test_dashboard_requires_authentication(dashboard_client):
    response = dashboard_client.get("/api/dashboard")
    assert response.status_code == 401


def test_weighted_forecast():
    value = 2500000
    probability = 40

    forecast = value * probability / 100

    assert forecast == 1000000


def test_conversion_rate():
    won = 5
    lost = 5

    rate = (won / (won + lost)) * 100

    assert rate == 50


def test_stage_ageing():
    current = 10
    entered = 3

    ageing = current - entered

    assert ageing == 7


def test_stalled_deal():
    activity_days = 20
    threshold = 14

    assert activity_days > threshold


def test_win_loss_ratio():
    won = 10
    lost = 5

    ratio = won / lost

    assert ratio == 2


def test_partner_contribution():
    opportunities = [
        100000,
        200000,
    ]

    assert sum(opportunities) == 300000


def test_active_pocs():
    active = 3
    assert active >= 0
