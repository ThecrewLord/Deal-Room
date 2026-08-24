import os

import pytest

from app.auth.password import hash_password
from app.constants.roles import AVAILABLE_ROLES
from app.models.auth.user import User
from app.models.auth.user_role import UserRole


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase1.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase1-test-secret")

    # Import after test configuration is set.
    from app import create_app
    from app.database import db

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        user = User(
            full_name="Single Role",
            email="single@example.com",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        user.roles.append(UserRole(role="Sales Executive"))

        multi = User(
            full_name="Multi Role",
            email="multi@example.com",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        multi.roles.extend([
            UserRole(role="Sales Executive"),
            UserRole(role="Solution Engineer"),
        ])

        db.session.add_all([user, multi])
        db.session.commit()

    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    return response


def test_canonical_roles_are_exactly_six():
    assert AVAILABLE_ROLES == [
        "Admin",
        "Sales Executive",
        "Sales Manager",
        "Pre-Sales Manager",
        "Solution Engineer",
        "Delivery",
    ]


def test_single_role_login_sets_active_role(client):
    data = login(client, "single@example.com").get_json()

    assert data.get("requires_role_selection") is not True
    assert data["active_role"] == "Sales Executive"
    assert data["user"]["roles"] == ["Sales Executive"]


def test_multi_role_login_requires_selection_and_returns_refresh_token(client):
    data = login(client, "multi@example.com").get_json()

    assert data["requires_role_selection"] is True
    assert data["roles"] == ["Sales Executive", "Solution Engineer"]
    assert data["refresh_token"]


def test_multi_role_selection_sets_selected_active_role(client):
    data = login(client, "multi@example.com").get_json()

    selected = client.post(
        "/api/auth/select-role",
        json={"role": "Solution Engineer"},
        headers={"Authorization": f"Bearer {data['refresh_token']}"},
    )

    assert selected.status_code == 200
    selected_data = selected.get_json()
    assert selected_data["active_role"] == "Solution Engineer"
    assert selected_data["access_token"]
    assert selected_data["refresh_token"]


def test_unassigned_role_selection_is_rejected(client):
    data = login(client, "single@example.com").get_json()

    selected = client.post(
        "/api/auth/select-role",
        json={"role": "Admin"},
        headers={"Authorization": f"Bearer {data['refresh_token']}"},
    )

    assert selected.status_code == 403
    assert selected.get_json()["message"] == "Invalid role."


def test_delivery_and_manager_roles_are_valid():
    assert "Delivery" in AVAILABLE_ROLES
    assert "Sales Manager" in AVAILABLE_ROLES
    assert "Pre-Sales Manager" in AVAILABLE_ROLES
    assert "Pre-Sales Consultant" not in AVAILABLE_ROLES
