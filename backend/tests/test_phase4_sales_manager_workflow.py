import pytest

from app.auth.password import hash_password
from app.constants.roles import (
    ADMIN,
    DELIVERY,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
)
from app.constants.stages import (
    APPROVED_STATUS,
    OPEN_STATUS,
    PENDING_SALES_MANAGER_REVIEW_STATUS,
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
from app.models.system.notification import Notification
from app.models.system.audit_log import AuditLog


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase4.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase4-test-secret")

    from app import create_app

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        stages = [
            StageMaster(stage_name="Lead / Identified", display_order=1),
            StageMaster(stage_name="Qualification", display_order=2),
            StageMaster(stage_name="Discovery", display_order=3),
            StageMaster(stage_name="POC / Technical Evaluation", display_order=4, requires_poc=True),
            StageMaster(stage_name="Proposal", display_order=5),
            StageMaster(stage_name="Negotiation", display_order=6),
            StageMaster(stage_name="Closed Won", display_order=7, is_closed=True, is_won=True),
            StageMaster(stage_name="Closed Lost", display_order=8, is_closed=True),
        ]
        db.session.add_all(stages)
        db.session.flush()

        def make_user(name, email, role, extra_roles=None, active=True, status="APPROVED"):
            user = User(
                full_name=name,
                email=email,
                password_hash=hash_password("Password123!"),
                status=status,
                active=active,
            )
            user.roles.append(UserRole(role=role))
            for extra in extra_roles or []:
                user.roles.append(UserRole(role=extra))
            db.session.add(user)
            db.session.flush()
            return user

        admin = make_user("Admin", "admin4@example.com", ADMIN)
        creator = make_user("Creator", "creator4@example.com", SALES_EXECUTIVE)
        owner = make_user("Owner", "owner4@example.com", SALES_EXECUTIVE)
        manager = make_user("Manager", "manager4@example.com", SALES_MANAGER)
        presales = make_user("Pre Sales", "psm4@example.com", PRE_SALES_MANAGER)
        se = make_user("SE", "se4@example.com", SOLUTION_ENGINEER)
        delivery = make_user("Delivery", "delivery4@example.com", DELIVERY)
        inactive_owner = make_user("Inactive Owner", "inactive4@example.com", SALES_EXECUTIVE, active=False)
        multi = make_user("Multi", "multi4@example.com", SALES_EXECUTIVE, extra_roles=[SOLUTION_ENGINEER])

        account = Account(account_name="Phase4 Account")
        db.session.add(account)
        db.session.flush()

        opportunity = Opportunity(
            account_id=account.account_id,
            created_by=creator.user_id,
            stage_id=stages[0].stage_id,
            opportunity_name="Phase 4 Opportunity",
            description="Reviewable opportunity",
            estimated_value=100000,
            probability=40,
            status=OPEN_STATUS,
            is_active=True,
        )
        db.session.add(opportunity)
        db.session.flush()
        db.session.add(OpportunityTeam(
            opportunity_id=opportunity.opportunity_id,
            user_id=creator.user_id,
            role=SALES_EXECUTIVE,
        ))
        db.session.add(StageHistory(
            opportunity_id=opportunity.opportunity_id,
            stage_id=stages[0].stage_id,
            changed_by=creator.user_id,
            remarks="Initial stage.",
        ))
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


def test_sales_executive_qualifies_and_submits(client, app):
    token = login(client, "creator4@example.com")
    with app.app_context():
        opp = Opportunity.query.filter_by(opportunity_name="Phase 4 Opportunity").first()
        oid = opp.opportunity_id

    assert client.post(f"/api/opportunities/{oid}/qualify", headers=auth(token)).status_code == 200
    with app.app_context():
        opp = db.session.get(Opportunity, oid)
        assert opp.current_stage.stage_name == "Qualification"
        assert opp.status == OPEN_STATUS
        assert any(a.action == "OPPORTUNITY_QUALIFIED" for a in __import__("app.models.system.audit_log", fromlist=["AuditLog"]).AuditLog.query.filter_by(entity_id=oid).all())

    response = client.post(f"/api/opportunities/{oid}/submit-for-review", headers=auth(token))
    assert response.status_code == 200

    with app.app_context():
        opp = db.session.get(Opportunity, oid)
        assert opp.status == PENDING_SALES_MANAGER_REVIEW_STATUS
        assert opp.is_active is True
        assert opp.sales_owner_id is None
        assert Notification.query.filter_by(
            notification_type="OPPORTUNITY_SUBMITTED_FOR_REVIEW"
        ).count() == 1


def test_sales_executive_is_locked_after_submission(client, app):
    token = login(client, "creator4@example.com")
    with app.app_context():
        opp = db.session.get(Opportunity, 1)
        oid = opp.opportunity_id
        opp.stage_id = StageMaster.query.filter_by(stage_name="Qualification").first().stage_id
        opp.status = PENDING_SALES_MANAGER_REVIEW_STATUS
        db.session.commit()

    response = client.put(
        f"/api/opportunities/{oid}",
        headers=auth(token),
        json={
            "estimated_value": 999999,
            "probability": 90,
            "expected_close_date": "2027-01-01",
            "updated_at": "2026-08-12T10:00:00",
        },
    )
    assert response.status_code == 403


@pytest.mark.parametrize("email,action", [
    ("creator4@example.com", "approve"),
    ("se4@example.com", "approve"),
    ("delivery4@example.com", "reject"),
    ("admin4@example.com", "approve"),
])
def test_unauthorized_roles_cannot_decide(client, app, email, action):
    creator_token = login(client, "creator4@example.com")
    with app.app_context():
        oid = db.session.get(Opportunity, 1).opportunity_id
        opp = db.session.get(Opportunity, oid)
        opp.stage_id = StageMaster.query.filter_by(stage_name="Qualification").first().stage_id
        opp.status = PENDING_SALES_MANAGER_REVIEW_STATUS
        db.session.commit()

    token = login(client, email)
    payload = {
        "decision": "APPROVE" if action == "approve" else "REJECT",
        "sales_owner_id": 3,
        "reason": "Not suitable",
        "updated_at": "2026-08-12T10:00:00",
    }
    assert client.post(f"/api/opportunities/{oid}/review", headers=auth(token), json=payload).status_code == 403


def test_manager_approval_assigns_owner_and_is_final(client, app):
    manager_token = login(client, "manager4@example.com")
    with app.app_context():
        oid = db.session.get(Opportunity, 1).opportunity_id
        opp = db.session.get(Opportunity, oid)
        opp.stage_id = StageMaster.query.filter_by(stage_name="Qualification").first().stage_id
        opp.status = PENDING_SALES_MANAGER_REVIEW_STATUS
        db.session.commit()
        updated_at = opp.updated_at.isoformat()

    response = client.post(
        f"/api/opportunities/{oid}/review",
        headers=auth(manager_token),
        json={"decision": "APPROVE", "sales_owner_id": 3, "updated_at": updated_at},
    )
    assert response.status_code == 200

    with app.app_context():
        opp = db.session.get(Opportunity, oid)
        assert opp.status == APPROVED_STATUS
        assert opp.sales_owner_id == 3
        assert OpportunityTeam.query.filter_by(opportunity_id=oid, user_id=3, role=SALES_EXECUTIVE).first()
        assert Notification.query.filter_by(
            notification_type="SALES_OWNER_ASSIGNED",
            recipient_user_id=3,
        ).count() == 1

    # Final decision: second decision is rejected.
    response = client.post(
        f"/api/opportunities/{oid}/review",
        headers=auth(manager_token),
        json={"decision": "REJECT", "reason": "Too late", "updated_at": updated_at},
    )
    assert response.status_code == 403


def test_manager_approval_hands_off_to_pre_sales(client, app):
    manager_token = login(client, "manager4@example.com")
    with app.app_context():
        oid = db.session.get(Opportunity, 1).opportunity_id
        opp = db.session.get(Opportunity, oid)
        opp.stage_id = StageMaster.query.filter_by(stage_name="Qualification").first().stage_id
        opp.status = PENDING_SALES_MANAGER_REVIEW_STATUS
        db.session.commit()
        updated_at = opp.updated_at.isoformat()

    response = client.post(
        f"/api/opportunities/{oid}/review",
        headers=auth(manager_token),
        json={"decision": "APPROVE", "sales_owner_id": 3, "updated_at": updated_at},
    )
    assert response.status_code == 200

    with app.app_context():
        assert Notification.query.filter_by(
            notification_type="OPPORTUNITY_SENT_TO_PRE_SALES",
            recipient_user_id=5,
            entity_id=oid,
        ).count() == 1
        assert AuditLog.query.filter_by(
            action="OPPORTUNITY_SENT_TO_PRE_SALES",
            entity_id=oid,
        ).count() == 1


def test_manager_rejection_requires_reason_and_keeps_record(client, app):
    manager_token = login(client, "manager4@example.com")
    with app.app_context():
        oid = db.session.get(Opportunity, 1).opportunity_id
        opp = db.session.get(Opportunity, oid)
        opp.stage_id = StageMaster.query.filter_by(stage_name="Qualification").first().stage_id
        opp.status = PENDING_SALES_MANAGER_REVIEW_STATUS
        db.session.commit()
        updated_at = opp.updated_at.isoformat()

    response = client.post(
        f"/api/opportunities/{oid}/review",
        headers=auth(manager_token),
        json={"decision": "REJECT", "updated_at": updated_at},
    )
    assert response.status_code == 400

    response = client.post(
        f"/api/opportunities/{oid}/review",
        headers=auth(manager_token),
        json={"decision": "REJECT", "reason": "Insufficient qualification evidence", "updated_at": updated_at},
    )
    assert response.status_code == 200

    with app.app_context():
        opp = db.session.get(Opportunity, oid)
        assert opp.status == REJECTED_STATUS
        assert opp.is_active is False
        assert db.session.get(Opportunity, oid) is not None
        assert Notification.query.filter_by(
            notification_type="OPPORTUNITY_REJECTED",
            recipient_user_id=2,
        ).count() == 1


def test_sales_owner_validation_and_review_queue_scope(client, app):
    manager_token = login(client, "manager4@example.com")
    with app.app_context():
        oid = db.session.get(Opportunity, 1).opportunity_id
        opp = db.session.get(Opportunity, oid)
        opp.stage_id = StageMaster.query.filter_by(stage_name="Qualification").first().stage_id
        opp.status = PENDING_SALES_MANAGER_REVIEW_STATUS
        db.session.commit()
        updated_at = opp.updated_at.isoformat()

    assert client.get("/api/opportunities/review-queue", headers=auth(manager_token)).status_code == 200
    assert client.get("/api/opportunities/review-queue", headers=auth(login(client, "creator4@example.com"))).status_code == 403

    response = client.post(
        f"/api/opportunities/{oid}/review",
        headers=auth(manager_token),
        json={"decision": "APPROVE", "sales_owner_id": 8, "updated_at": updated_at},
    )
    assert response.status_code in (400, 403)


def test_active_role_controls_phase4_actions(client, app):
    response = client.post(
        "/api/auth/login",
        json={"email": "multi4@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    refresh = response.get_json()["refresh_token"]

    selected = client.post(
        "/api/auth/select-role",
        json={"role": SOLUTION_ENGINEER},
        headers=auth(refresh),
    )
    assert selected.status_code == 200

    with app.app_context():
        oid = db.session.get(Opportunity, 1).opportunity_id

    response = client.post(
        f"/api/opportunities/{oid}/qualify",
        headers=auth(selected.get_json()["access_token"]),
    )
    assert response.status_code == 403
