import pytest

from app import create_app
from app.auth.password import hash_password
from app.constants.activity_types import (
    USER_APPROVED,
    USER_ROLE_ADDED,
    USER_ROLE_REMOVED,
)
from app.constants.roles import (
    ADMIN,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
)
from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.system.audit_log import AuditLog


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase9.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase9-test-secret")

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        def user(name, email, roles, status="APPROVED", active=True):
            u = User(
                full_name=name,
                email=email,
                password_hash=hash_password("Password123!"),
                status=status,
                active=active,
            )
            for role in roles:
                u.roles.append(UserRole(role=role))
            db.session.add(u)
            db.session.flush()
            return u

        admin = user("Admin", "admin9@example.com", [ADMIN])
        sales_manager = user("Sales Manager", "sm9@example.com", [SALES_MANAGER])
        psm = user("Pre Sales Manager", "psm9@example.com", [PRE_SALES_MANAGER])
        se = user("SE", "se9@example.com", [SOLUTION_ENGINEER])
        se.manager_id = psm.user_id
        sales = user("Sales", "sales9@example.com", [SALES_EXECUTIVE])
        sales.manager_id = sales_manager.user_id
        pending = user("Pending", "pending9@example.com", [], status="PENDING")

        db.session.commit()

        application.config["P9"] = {
            "admin": admin.user_id,
            "sm": sales_manager.user_id,
            "psm": psm.user_id,
            "se": se.user_id,
            "sales": sales.user_id,
            "pending": pending.user_id,
        }

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
    return response.get_json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_user_list_contains_manager_and_organization(client, app):
    session = login(client, "admin9@example.com")
    response = client.get(
        "/api/auth/admin/users",
        headers=auth(session["access_token"]),
    )
    assert response.status_code == 200

    row = next(
        x for x in response.get_json()
        if x["user_id"] == app.config["P9"]["se"]
    )
    assert row["manager_name"] == "Pre Sales Manager"
    assert row["organization"] == "PRE_SALES_TECHNICAL"


def test_manager_candidates_are_filtered(client, app):
    session = login(client, "admin9@example.com")
    response = client.get(
        f"/api/auth/admin/users/{app.config['P9']['se']}/manager-candidates"
        f"?role={SOLUTION_ENGINEER}",
        headers=auth(session["access_token"]),
    )
    assert response.status_code == 200
    assert [x["full_name"] for x in response.get_json()] == ["Pre Sales Manager"]


def test_manager_change_and_audit(client, app):
    session = login(client, "admin9@example.com")
    with app.app_context():
        updated = User.query.get(app.config["P9"]["se"]).updated_at.isoformat()

    response = client.patch(
        f"/api/auth/admin/users/{app.config['P9']['se']}/manager",
        headers=auth(session["access_token"]),
        json={
            "manager_id": app.config["P9"]["psm"],
            "updated_at": updated,
        },
    )
    assert response.status_code == 200


def test_invalid_manager_self_and_nonmanager_rejected(client, app):
    session = login(client, "admin9@example.com")

    with app.app_context():
        updated = User.query.get(app.config["P9"]["se"]).updated_at.isoformat()

    response = client.patch(
        f"/api/auth/admin/users/{app.config['P9']['se']}/manager",
        headers=auth(session["access_token"]),
        json={
            "manager_id": app.config["P9"]["se"],
            "updated_at": updated,
        },
    )
    assert response.status_code == 400

    with app.app_context():
        updated = User.query.get(app.config["P9"]["se"]).updated_at.isoformat()

    response = client.patch(
        f"/api/auth/admin/users/{app.config['P9']['se']}/manager",
        headers=auth(session["access_token"]),
        json={
            "manager_id": app.config["P9"]["sales"],
            "updated_at": updated,
        },
    )
    assert response.status_code == 400


def test_non_admin_cannot_manage_users(client, app):
    session = login(client, "se9@example.com")

    assert client.get(
        "/api/auth/admin/users",
        headers=auth(session["access_token"]),
    ).status_code == 403

    assert client.patch(
        f"/api/auth/admin/users/{app.config['P9']['se']}/manager",
        headers=auth(session["access_token"]),
        json={"manager_id": app.config["P9"]["psm"]},
    ).status_code == 403


def test_approval_requires_manager_and_records_audit(client, app):
    session = login(client, "admin9@example.com")

    response = client.post(
        f"/api/auth/admin/approve/{app.config['P9']['pending']}",
        headers=auth(session["access_token"]),
        json={"roles": [SOLUTION_ENGINEER]},
    )
    assert response.status_code == 400

    response = client.post(
        f"/api/auth/admin/approve/{app.config['P9']['pending']}",
        headers=auth(session["access_token"]),
        json={
            "roles": [SOLUTION_ENGINEER],
            "manager_id": app.config["P9"]["psm"],
        },
    )
    assert response.status_code == 200

    with app.app_context():
        u = User.query.get(app.config["P9"]["pending"])
        assert u.manager_id == app.config["P9"]["psm"]
        assert AuditLog.query.filter_by(
            entity_id=u.user_id,
            action=USER_APPROVED,
        ).count() == 1


def test_role_change_cannot_break_subordinates(client, app):
    session = login(client, "admin9@example.com")

    with app.app_context():
        updated = User.query.get(app.config["P9"]["psm"]).updated_at.isoformat()

    response = client.post(
        f"/api/auth/admin/users/{app.config['P9']['psm']}/roles",
        headers=auth(session["access_token"]),
        json={
            "roles": [SOLUTION_ENGINEER],
            "manager_id": None,
            "updated_at": updated,
        },
    )
    assert response.status_code == 400


def test_revocation_cannot_break_subordinates(client, app):
    session = login(client, "admin9@example.com")
    response = client.post(
        f"/api/auth/admin/revoke/{app.config['P9']['psm']}",
        headers=auth(session["access_token"]),
    )
    assert response.status_code == 400


def test_manager_cycle_is_rejected(client, app):
    session = login(client, "admin9@example.com")

    with app.app_context():
        updated = User.query.get(app.config["P9"]["sales"]).updated_at.isoformat()

    response = client.patch(
        f"/api/auth/admin/users/{app.config['P9']['sales']}/manager",
        headers=auth(session["access_token"]),
        json={
            "manager_id": app.config["P9"]["sales"],
            "updated_at": updated,
        },
    )
    assert response.status_code == 400


def test_role_change_invalidates_token_and_audits(client, app):
    """
    V2 security contract:
    changing a user's actual role set increments auth_version, which
    invalidates all previously issued access tokens.
    """
    se_session = login(client, "se9@example.com")
    admin_session = login(client, "admin9@example.com")

    with app.app_context():
        user = User.query.get(app.config["P9"]["se"])
        updated = user.updated_at.isoformat()
        old_version = user.auth_version

    response = client.post(
        f"/api/auth/admin/users/{app.config['P9']['se']}/roles",
        headers=auth(admin_session["access_token"]),
        json={
            "roles": [PRE_SALES_MANAGER],
            "manager_id": None,
            "updated_at": updated,
        },
    )
    assert response.status_code == 200

    with app.app_context():
        user = User.query.get(app.config["P9"]["se"])
        assert user.auth_version == old_version + 1

        actions = {
            x.action
            for x in AuditLog.query.filter_by(
                entity_id=app.config["P9"]["se"]
            ).all()
        }

        assert USER_ROLE_ADDED in actions
        assert USER_ROLE_REMOVED in actions

    response = client.get(
        "/api/auth/me",
        headers=auth(se_session["access_token"]),
    )
    assert response.status_code == 401
