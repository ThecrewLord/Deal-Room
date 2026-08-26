import pytest
from datetime import datetime

from app import create_app
from app.auth.password import hash_password
from app.constants.activity_types import (
    USER_APPROVED,
    USER_ROLE_ADDED,
    USER_ROLE_REMOVED,
    USER_ACCESS_REVOKED,
    OPPORTUNITY_STAGE_CHANGED,
)
from app.constants.roles import ADMIN, SALES_EXECUTIVE, SALES_MANAGER, PRE_SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY
from app.constants.stages import OPEN_STATUS, INITIAL_STAGE_NAME
from app.database import db
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.account.account import Account
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster
from app.models.system.audit_log import AuditLog
from app.services.auth_service import AuthService
from app.services.opportunity_service import OpportunityService


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase8.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase8-test-secret")
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        db.drop_all()
        db.create_all()
        stages = [
            StageMaster(stage_name="Lead / Identified", display_order=1, requires_poc=False, is_closed=False, is_won=False),
            StageMaster(stage_name="Qualification", display_order=2, requires_poc=False, is_closed=False, is_won=False),
            StageMaster(stage_name="Discovery", display_order=3, requires_poc=False, is_closed=False, is_won=False),
            StageMaster(stage_name="POC / Technical Evaluation", display_order=4, requires_poc=True, is_closed=False, is_won=False),
            StageMaster(stage_name="Proposal", display_order=5, requires_poc=False, is_closed=False, is_won=False),
            StageMaster(stage_name="Negotiation", display_order=6, requires_poc=False, is_closed=False, is_won=False),
            StageMaster(stage_name="Closed Won", display_order=7, requires_poc=False, is_closed=True, is_won=True),
            StageMaster(stage_name="Closed Lost", display_order=8, requires_poc=False, is_closed=True, is_won=False),
        ]
        db.session.add_all(stages)
        db.session.flush()

        def user(name, email, role, extra=None):
            u = User(full_name=name, email=email, password_hash=hash_password("Password123!"), status="APPROVED", active=True)
            u.roles.append(UserRole(role=role))
            for r in extra or []:
                u.roles.append(UserRole(role=r))
            db.session.add(u)
            db.session.flush()
            return u

        admin = user("Admin", "admin8@example.com", ADMIN)
        admin2 = user("Admin 2", "admin2-8@example.com", ADMIN)
        sales = user("Sales", "sales8@example.com", SALES_EXECUTIVE)
        manager = user("Manager", "manager8@example.com", SALES_MANAGER)
        psm = user("Pre-Sales Manager", "psm8@example.com", PRE_SALES_MANAGER)
        se = user("SE", "se8@example.com", SOLUTION_ENGINEER)
        se.manager_id = psm.user_id
        delivery = user("Delivery", "delivery8@example.com", DELIVERY)
        delivery.manager_id = psm.user_id
        pending = User(full_name="Pending", email="pending8@example.com", password_hash=hash_password("Password123!"), status="PENDING", active=True)
        db.session.add(pending)
        account = Account(account_name="Phase 8 Account")
        db.session.add(account)
        db.session.flush()

        opportunity = Opportunity(account_id=account.account_id, created_by=sales.user_id, stage_id=stages[0].stage_id, opportunity_name="Phase 8 Opportunity", status=OPEN_STATUS, is_active=True)
        db.session.add(opportunity)
        db.session.flush()
        db.session.add(OpportunityTeam(opportunity_id=opportunity.opportunity_id, user_id=sales.user_id, role=SALES_EXECUTIVE))
        db.session.commit()

        application.config["P8"] = {
            "admin": admin.user_id,
            "admin2": admin2.user_id,
            "sales": sales.user_id,
            "manager": manager.user_id,
            "psm": psm.user_id,
            "se": se.user_id,
            "delivery": delivery.user_id,
            "pending": pending.user_id,
            "opportunity": opportunity.opportunity_id,
        }
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert response.status_code == 200
    return response.get_json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_pending_approval_creates_user_approved_audit(client, app):
    session = login(client, "admin8@example.com")
    r = client.post(f"/api/auth/admin/approve/{app.config['P8']['pending']}", headers=auth(session["access_token"]), json={"roles": [SALES_EXECUTIVE]})
    assert r.status_code == 200
    with app.app_context():
        log = AuditLog.query.filter_by(entity_id=app.config["P8"]["pending"], action=USER_APPROVED).first()
        assert log is not None
        assert log.performed_by == app.config["P8"]["admin"]
        assert "approved" in log.description.lower()


def test_approval_is_pending_only(client, app):
    session = login(client, "admin8@example.com")
    r = client.post(f"/api/auth/admin/approve/{app.config['P8']['sales']}", headers=auth(session["access_token"]), json={"roles": [SALES_EXECUTIVE]})
    assert r.status_code == 409


def test_role_changes_are_audited_and_invalidate_old_token(client, app):
    session = login(client, "se8@example.com")
    old_token = session["access_token"]
    with app.app_context():
        user = User.query.get(app.config["P8"]["se"])
        updated_at = user.updated_at.isoformat()
    admin = login(client, "admin8@example.com")
    r = client.post(f"/api/auth/admin/users/{app.config['P8']['se']}/roles", headers=auth(admin["access_token"]), json={"roles": [DELIVERY], "manager_id": app.config["P8"]["psm"], "updated_at": updated_at})
    assert r.status_code == 200
    stale = client.get("/api/dashboard", headers=auth(old_token))
    assert stale.status_code == 401
    with app.app_context():
        actions = {row.action for row in AuditLog.query.filter_by(entity_id=app.config["P8"]["se"]).all()}
        assert USER_ROLE_ADDED in actions
        assert USER_ROLE_REMOVED in actions


def test_revocation_is_audited_and_login_is_denied(client, app):
    admin = login(client, "admin8@example.com")
    r = client.post(f"/api/auth/admin/revoke/{app.config['P8']['sales']}", headers=auth(admin["access_token"]))
    assert r.status_code == 200
    with app.app_context():
        log = AuditLog.query.filter_by(entity_id=app.config["P8"]["sales"], action=USER_ACCESS_REVOKED).first()
        assert log is not None
    denied = client.post("/api/auth/login", json={"email": "sales8@example.com", "password": "Password123!"})
    assert denied.status_code == 403


def test_admin_business_isolation(client, app):
    admin = login(client, "admin8@example.com")
    headers = auth(admin["access_token"])
    assert client.get("/api/dashboard", headers=headers).status_code == 403
    assert client.get("/api/opportunities", headers=headers).status_code == 403
    assert client.get(f"/api/opportunities/{app.config['P8']['opportunity']}", headers=headers).status_code == 403
    assert client.get("/api/accounts", headers=headers).status_code == 403
    assert client.get("/api/poc/1", headers=headers).status_code == 403


def test_last_admin_protection(client, app):
    admin = login(client, "admin8@example.com")
    with app.app_context():
        user = User.query.get(app.config["P8"]["admin"])
        updated_at = user.updated_at.isoformat()
    r = client.post(f"/api/auth/admin/users/{app.config['P8']['admin']}/roles", headers=auth(admin["access_token"]), json={"roles": [SALES_EXECUTIVE], "updated_at": updated_at})
    assert r.status_code == 403
    r = client.post(f"/api/auth/admin/revoke/{app.config['P8']['admin']}", headers=auth(admin["access_token"]))
    assert r.status_code == 403


def test_qualification_writes_stage_audit(client, app):
    session = login(client, "sales8@example.com")
    oid = app.config["P8"]["opportunity"]
    r = client.post(f"/api/opportunities/{oid}/qualify", headers=auth(session["access_token"]))
    assert r.status_code == 200
    with app.app_context():
        assert AuditLog.query.filter_by(entity_id=oid, action=OPPORTUNITY_STAGE_CHANGED).count() == 1


def test_multi_role_selection_rejects_stale_refresh(client, app):
    with app.app_context():
        user = User.query.get(app.config["P8"]["se"])
        user.roles.append(UserRole(role=DELIVERY))
        db.session.commit()
    login_response = login(client, "se8@example.com")
    assert login_response["requires_role_selection"]
    admin = login(client, "admin8@example.com")
    with app.app_context():
        user = User.query.get(app.config["P8"]["se"])
        updated_at = user.updated_at.isoformat()
    r = client.post(f"/api/auth/admin/users/{app.config['P8']['se']}/roles", headers=auth(admin["access_token"]), json={"roles": [SOLUTION_ENGINEER], "updated_at": updated_at})
    assert r.status_code == 200
    selected = client.post("/api/auth/select-role", headers=auth(login_response["refresh_token"]), json={"role": DELIVERY})
    assert selected.status_code == 401
