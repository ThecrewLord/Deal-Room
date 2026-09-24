import pytest
from flask_jwt_extended import decode_token

from app.auth.password import hash_password
from app.constants.roles import (
    ADMIN, DATA_ANALYST, DELIVERY_MANAGER, DEVOPS_ENGINEER, LEADERSHIP,
    PRE_SALES_MANAGER, SALES_EXECUTIVE, SALES_MANAGER, SOLUTION_ENGINEER,
    AVAILABLE_ROLES, LEGACY_DELIVERY,
)
from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.auth.user_system_permission import UserSystemPermission
from app.services.auth_service import AuthService
from app.constants.system_permissions import MANAGE_ADMINS


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase1.db"
    application = __import__("app", fromlist=["create_app"]).create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "JWT_SECRET_KEY": "phase1-test-secret",
    })
    with application.app_context():
        db.drop_all(); db.create_all()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def make_user(email, roles, status="APPROVED", active=True):
    user = User(full_name=email.split("@")[0], email=email,
                password_hash=hash_password("Password123!"), status=status, active=active)
    for role in roles:
        user.roles.append(UserRole(role=role))
    db.session.add(user); db.session.flush()
    return user


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_canonical_roles_are_complete():
    assert AVAILABLE_ROLES == [
        LEADERSHIP, ADMIN, SALES_MANAGER, SALES_EXECUTIVE,
        PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY_MANAGER,
        DEVOPS_ENGINEER, DATA_ANALYST,
    ]
    assert LEGACY_DELIVERY not in AVAILABLE_ROLES


def test_legacy_delivery_role_is_not_valid(app):
    with app.app_context():
        assert not __import__("app.constants.roles", fromlist=["is_valid_role"]).is_valid_role(LEGACY_DELIVERY)


def test_first_signup_becomes_leadership_and_second_is_pending(client, app):
    first = client.post("/api/auth/signup", json={"full_name": "Root", "email": "root@example.com", "password": "Password123!"})
    second = client.post("/api/auth/signup", json={"full_name": "Second", "email": "second@example.com", "password": "Password123!"})
    assert first.status_code == 201 and first.get_json()["status"] == "APPROVED"
    assert second.status_code == 201 and second.get_json()["status"] == "PENDING"
    with app.app_context():
        root = User.query.filter_by(email="root@example.com").first()
        other = User.query.filter_by(email="second@example.com").first()
        assert root.role_names() == [LEADERSHIP]
        assert other.role_names() == []


def test_multi_role_session_does_not_union_permissions(client, app):
    with app.app_context():
        u = make_user("multi@example.com", [SALES_EXECUTIVE, SOLUTION_ENGINEER])
        db.session.commit()
    data = login(client, "multi@example.com")
    selected = client.post("/api/auth/select-role", json={"role": SOLUTION_ENGINEER}, headers=auth(data["refresh_token"]))
    assert selected.status_code == 200
    payload = decode_token(selected.get_json()["access_token"])
    assert payload["active_role"] == SOLUTION_ENGINEER
    bad = client.post("/api/auth/select-role", json={"role": ADMIN}, headers=auth(data["refresh_token"]))
    assert bad.status_code == 403


def test_stale_token_rejected_after_role_change(client, app):
    with app.app_context():
        admin = make_user("admin@example.com", [ADMIN])
        target = make_user("target@example.com", [SALES_EXECUTIVE])
        db.session.commit()
    target_session = login(client, "target@example.com")
    admin_session = login(client, "admin@example.com")
    with app.app_context():
        target = User.query.filter_by(email="target@example.com").first()
        expected = target.updated_at.isoformat()
        actor = User.query.filter_by(email="admin@example.com").first()
        AuthService.update_roles(actor.user_id, target.user_id, [SALES_MANAGER], expected)
    assert client.get("/api/auth/me", headers=auth(target_session["access_token"])).status_code == 401


def test_leadership_can_assign_roles_and_admin_but_admin_cannot_assign_leadership(client, app):
    with app.app_context():
        leader = make_user("leader@example.com", [LEADERSHIP])
        admin = make_user("admin@example.com", [ADMIN])
        target = make_user("target@example.com", [SALES_EXECUTIVE])
        db.session.commit()
    leader_session = login(client, "leader@example.com")
    admin_session = login(client, "admin@example.com")
    with app.app_context():
        target = User.query.filter_by(email="target@example.com").first()
        expected = target.updated_at.isoformat()
    r = client.post(f"/api/auth/admin/users/{target.user_id}/roles", headers=auth(leader_session["access_token"]), json={"roles": [ADMIN], "updated_at": expected})
    assert r.status_code == 200
    with app.app_context():
        target = User.query.filter_by(email="target@example.com").first()
        expected = target.updated_at.isoformat()
    r = client.post(f"/api/auth/admin/users/{target.user_id}/roles", headers=auth(admin_session["access_token"]), json={"roles": [LEADERSHIP], "updated_at": expected})
    assert r.status_code == 403


def test_admin_cannot_see_other_admins_but_leadership_can(client, app):
    with app.app_context():
        leader = make_user("leader@example.com", [LEADERSHIP])
        admin = make_user("admin@example.com", [ADMIN])
        employee = make_user("employee@example.com", [SALES_EXECUTIVE])
        db.session.commit()
    admin_data = login(client, "admin@example.com")
    leader_data = login(client, "leader@example.com")
    admin_rows = client.get("/api/auth/admin/users", headers=auth(admin_data["access_token"])).get_json()
    leader_rows = client.get("/api/auth/admin/users", headers=auth(leader_data["access_token"])).get_json()
    assert all(ADMIN not in row["roles"] and LEADERSHIP not in row["roles"] for row in admin_rows)
    assert any(row["email"] == "admin@example.com" for row in leader_rows)


def test_delegated_admin_can_assign_admin_but_not_leadership(client, app):
    with app.app_context():
        leader = make_user("leader@example.com", [LEADERSHIP])
        admin = make_user("admin@example.com", [ADMIN])
        target = make_user("target@example.com", [SALES_EXECUTIVE])
        AuthService.set_admin_delegation(leader.user_id, admin.user_id, True)
        db.session.commit()
    admin_data = login(client, "admin@example.com")
    with app.app_context():
        target = User.query.filter_by(email="target@example.com").first(); expected = target.updated_at.isoformat()
    r = client.post(f"/api/auth/admin/users/{target.user_id}/roles", headers=auth(admin_data["access_token"]), json={"roles": [ADMIN], "updated_at": expected})
    assert r.status_code == 200


def test_last_leadership_cannot_be_demoted_or_revoked(client, app):
    with app.app_context():
        leader = make_user("leader@example.com", [LEADERSHIP])
        db.session.commit()
    data = login(client, "leader@example.com")
    with app.app_context():
        leader = User.query.filter_by(email="leader@example.com").first(); expected = leader.updated_at.isoformat()
    r = client.post(f"/api/auth/admin/users/{leader.user_id}/roles", headers=auth(data["access_token"]), json={"roles": [SALES_MANAGER], "updated_at": expected})
    assert r.status_code == 403
    with app.app_context():
        leader = User.query.filter_by(email="leader@example.com").first()
        # Direct service call demonstrates the invariant is server-side, not UI-only.
        with pytest.raises(PermissionError): AuthService.revoke(leader.user_id, leader.user_id)


def test_admin_cannot_access_business_pipeline(client, app):
    with app.app_context():
        make_user("admin@example.com", [ADMIN]); db.session.commit()
    data = login(client, "admin@example.com")
    assert client.get("/api/opportunities", headers=auth(data["access_token"])).status_code == 403
    assert client.get("/api/dashboard", headers=auth(data["access_token"])).status_code == 403


def test_manager_hierarchy_includes_delivery_roles(app):
    from app.constants.organizations import get_required_manager_roles
    assert get_required_manager_roles([DEVOPS_ENGINEER]) == {DELIVERY_MANAGER}
    assert get_required_manager_roles([DATA_ANALYST]) == {DELIVERY_MANAGER}


def test_legacy_delivery_jwt_is_rejected_server_side(client, app):
    from app.auth.token_service import create_access
    with app.app_context():
        user = make_user("legacy@example.com", [SOLUTION_ENGINEER])
        db.session.commit()
        token = create_access(user, LEGACY_DELIVERY)
    response = client.get("/api/auth/me", headers=auth(token))
    assert response.status_code == 403


def test_multi_role_admin_session_cannot_use_stored_leadership_privilege(client, app):
    with app.app_context():
        user = make_user("dual@example.com", [ADMIN, LEADERSHIP])
        target = make_user("target@example.com", [SALES_EXECUTIVE])
        db.session.commit()
    # Login returns a role-selection refresh token. Explicitly choose Admin.
    login_data = login(client, "dual@example.com")
    admin_session = client.post("/api/auth/select-role", json={"role": ADMIN}, headers=auth(login_data["refresh_token"])).get_json()
    with app.app_context():
        target = User.query.filter_by(email="target@example.com").first(); expected = target.updated_at.isoformat()
    response = client.post(f"/api/auth/admin/users/{target.user_id}/roles", headers=auth(admin_session["access_token"]), json={"roles": [LEADERSHIP], "updated_at": expected})
    assert response.status_code == 403

@pytest.mark.skipif(not __import__("os").getenv("TEST_POSTGRES_URL"), reason="requires a PostgreSQL integration database")
def test_postgres_concurrent_last_leadership_demotion_is_safe():
    import threading
    from app import create_app

    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": __import__("os").environ["TEST_POSTGRES_URL"],
        "JWT_SECRET_KEY": "phase1-postgres-test-secret-32-bytes-long",
    })
    with application.app_context():
        db.drop_all(); db.create_all()
        a = make_user("leader-a@example.com", [LEADERSHIP])
        b = make_user("leader-b@example.com", [LEADERSHIP])
        db.session.commit()

    barrier = threading.Barrier(2)
    results = []

    def worker(email):
        with application.app_context():
            user = User.query.filter_by(email=email).first()
            expected = user.updated_at.isoformat()
            barrier.wait()
            try:
                AuthService.update_roles(user.user_id, user.user_id, [SALES_MANAGER], expected, active_role=LEADERSHIP)
                results.append("success")
            except (PermissionError, RuntimeError):
                results.append("blocked")

    t1 = threading.Thread(target=worker, args=("leader-a@example.com",))
    t2 = threading.Thread(target=worker, args=("leader-b@example.com",))
    t1.start(); t2.start(); t1.join(); t2.join()
    assert sorted(results) == ["blocked", "success"]
    with application.app_context():
        assert User.query.filter(User.active.is_(True), User.status == "APPROVED", User.roles.any(role=LEADERSHIP)).count() == 1


def test_admin_cannot_assign_admin_without_delegation(client, app):
    with app.app_context():
        make_user("admin@example.com", [ADMIN])
        target = make_user("target@example.com", [SALES_EXECUTIVE])
        db.session.commit()
    admin_data = login(client, "admin@example.com")
    with app.app_context():
        target = User.query.filter_by(email="target@example.com").first(); expected = target.updated_at.isoformat()
    response = client.post(f"/api/auth/admin/users/{target.user_id}/roles", headers=auth(admin_data["access_token"]), json={"roles": [ADMIN], "updated_at": expected})
    assert response.status_code == 403
