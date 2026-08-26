import pytest

from app.auth.password import hash_password
from app.constants.activity_types import (
    DELIVERY_ASSIGNED,
    OPPORTUNITY_SENT_TO_PRE_SALES,
    PRE_SALES_ASSIGNMENT_FINALIZED,
    SOLUTION_ENGINEER_ASSIGNED,
)
from app.constants.roles import (
    ADMIN,
    DELIVERY,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
)
from app.constants.stages import APPROVED_STATUS
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster
from app.models.system.audit_log import AuditLog
from app.models.system.notification import Notification


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase5.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase5-test-secret")

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

        admin = make_user("Admin", "admin5@example.com", ADMIN)
        creator = make_user("Creator", "creator5@example.com", SALES_EXECUTIVE)
        owner = make_user("Sales Owner", "owner5@example.com", SALES_EXECUTIVE)
        sales_manager = make_user("Sales Manager", "manager5@example.com", SALES_MANAGER)
        presales = make_user("Pre Sales Manager", "psm5@example.com", PRE_SALES_MANAGER)
        se1 = make_user("SE One", "se1_5@example.com", SOLUTION_ENGINEER)
        se2 = make_user("SE Two", "se2_5@example.com", SOLUTION_ENGINEER)
        delivery1 = make_user("Delivery One", "delivery1_5@example.com", DELIVERY)
        delivery2 = make_user("Delivery Two", "delivery2_5@example.com", DELIVERY)
        inactive_se = make_user("Inactive SE", "inactive_se5@example.com", SOLUTION_ENGINEER, active=False)
        inactive_delivery = make_user("Inactive Delivery", "inactive_delivery5@example.com", DELIVERY, active=False)
        wrong = make_user("Sales Only", "wrong5@example.com", SALES_EXECUTIVE)
        multi_se_delivery = make_user(
            "SE Delivery Multi",
            "multi_se_delivery5@example.com",
            SOLUTION_ENGINEER,
            extra_roles=[DELIVERY],
        )
        multi_manager_se = make_user(
            "Manager SE Multi",
            "multi_manager_se5@example.com",
            PRE_SALES_MANAGER,
            extra_roles=[SOLUTION_ENGINEER],
        )

        account = Account(account_name="Phase 5 Account")
        db.session.add(account)
        db.session.flush()

        opportunity = Opportunity(
            account_id=account.account_id,
            created_by=creator.user_id,
            sales_owner_id=owner.user_id,
            stage_id=stages[1].stage_id,
            opportunity_name="Phase 5 Opportunity",
            description="Awaiting technical allocation",
            estimated_value=250000,
            probability=60,
            status=APPROVED_STATUS,
            is_active=True,
        )
        db.session.add(opportunity)
        db.session.flush()
        db.session.add_all([
            OpportunityTeam(opportunity_id=opportunity.opportunity_id, user_id=creator.user_id, role=SALES_EXECUTIVE),
            OpportunityTeam(opportunity_id=opportunity.opportunity_id, user_id=owner.user_id, role=SALES_EXECUTIVE),
        ])
        db.session.commit()

        # Simulate the Phase 4 handoff event/notification already having been
        # generated so Phase 5 can verify the complete handoff semantics.
        AuditLog(
            entity_type="Opportunity",
            entity_id=opportunity.opportunity_id,
            action=OPPORTUNITY_SENT_TO_PRE_SALES,
            description="Opportunity approved and handed to Pre-Sales Manager for technical team assignment.",
            performed_by=sales_manager.user_id,
        )
        db.session.add(Notification(
            recipient_user_id=presales.user_id,
            notification_type=OPPORTUNITY_SENT_TO_PRE_SALES,
            entity_type="Opportunity",
            entity_id=opportunity.opportunity_id,
            message="Opportunity 'Phase 5 Opportunity' requires technical team assignment.",
            is_read=False,
        ))
        db.session.commit()

        application.config["PHASE5_IDS"] = {
            "admin": admin.user_id,
            "creator": creator.user_id,
            "owner": owner.user_id,
            "sales_manager": sales_manager.user_id,
            "presales": presales.user_id,
            "se1": se1.user_id,
            "se2": se2.user_id,
            "delivery1": delivery1.user_id,
            "delivery2": delivery2.user_id,
            "inactive_se": inactive_se.user_id,
            "inactive_delivery": inactive_delivery.user_id,
            "wrong": wrong.user_id,
            "multi_se_delivery": multi_se_delivery.user_id,
            "multi_manager_se": multi_manager_se.user_id,
            "opportunity": opportunity.opportunity_id,
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


def token_for(client, email, role=None):
    session = login(client, email)
    if not session.get("requires_role_selection"):
        return session["access_token"]
    assert role
    selected = client.post(
        "/api/auth/select-role",
        json={"role": role},
        headers=auth(session["refresh_token"]),
    )
    assert selected.status_code == 200
    return selected.get_json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def opportunity_snapshot(app):
    with app.app_context():
        opportunity = Opportunity.query.filter_by(opportunity_name="Phase 5 Opportunity").first()
        return opportunity.opportunity_id, opportunity.updated_at.isoformat(), opportunity.status


def assignment_payload(app, se_ids, delivery_ids):
    oid, updated_at, _ = opportunity_snapshot(app)
    return oid, {
        "solution_engineer_ids": se_ids,
        "delivery_ids": delivery_ids,
        "updated_at": updated_at,
    }


def test_1_approved_opportunity_enters_pre_sales_queue(client, app):
    token = token_for(client, "psm5@example.com")
    response = client.get("/api/opportunities/pre-sales-assignment-queue", headers=auth(token))
    assert response.status_code == 200
    assert any(item["opportunity_id"] == app.config["PHASE5_IDS"]["opportunity"] for item in response.get_json())


def test_2_sales_executive_cannot_view_pre_sales_queue(client):
    token = token_for(client, "creator5@example.com")
    assert client.get("/api/opportunities/pre-sales-assignment-queue", headers=auth(token)).status_code == 403


def test_3_sales_manager_cannot_modify_technical_assignment(client, app):
    token = token_for(client, "manager5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 403


def test_4_solution_engineer_cannot_finalize(client, app):
    token = token_for(client, "se1_5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 403


def test_5_delivery_cannot_finalize(client, app):
    token = token_for(client, "delivery1_5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 403


def test_6_admin_cannot_finalize(client, app):
    token = token_for(client, "admin5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 403


def test_7_pre_sales_manager_can_retrieve_eligible_se_candidates(client):
    token = token_for(client, "psm5@example.com")
    response = client.get("/api/opportunities/pre-sales-assignment-candidates/Solution%20Engineer", headers=auth(token))
    assert response.status_code == 200
    ids = {item["user_id"] for item in response.get_json()}
    assert ids
    assert app.config["PHASE5_IDS"]["inactive_se"] not in ids


def test_8_pre_sales_manager_can_retrieve_eligible_delivery_candidates(client, app):
    token = token_for(client, "psm5@example.com")
    response = client.get("/api/opportunities/pre-sales-assignment-candidates/Delivery", headers=auth(token))
    assert response.status_code == 200
    ids = {item["user_id"] for item in response.get_json()}
    assert app.config["PHASE5_IDS"]["delivery1"] in ids
    assert app.config["PHASE5_IDS"]["inactive_delivery"] not in ids


def test_9_inactive_se_rejected(client, app):
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["inactive_se"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_10_inactive_delivery_rejected(client, app):
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["inactive_delivery"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_11_sales_executive_cannot_be_assigned_as_se(client, app):
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["wrong"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_12_sales_executive_cannot_be_assigned_as_delivery(client, app):
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["wrong"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_13_se_without_delivery_role_cannot_be_delivery_but_multi_role_user_can(client, app):
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["se1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400

    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["multi_se_delivery"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 200


def test_14_delivery_without_se_role_cannot_be_se(client, app):
    # Reset the opportunity after the previous test's successful assignment.
    with app.app_context():
        oid = app.config["PHASE5_IDS"]["opportunity"]
        opportunity = db.session.get(Opportunity, oid)
        for row in list(opportunity.team_members):
            if row.role in {SOLUTION_ENGINEER, DELIVERY}:
                db.session.delete(row)
        opportunity.status = APPROVED_STATUS
        db.session.commit()

    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["delivery1"]], [app.config["PHASE5_IDS"]["delivery2"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_15_multiple_se_and_delivery_users_succeed(client, app):
    with app.app_context():
        oid = app.config["PHASE5_IDS"]["opportunity"]
        opportunity = db.session.get(Opportunity, oid)
        for row in list(opportunity.team_members):
            if row.role in {SOLUTION_ENGINEER, DELIVERY}:
                db.session.delete(row)
        opportunity.status = APPROVED_STATUS
        db.session.commit()

    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(
        app,
        [app.config["PHASE5_IDS"]["se1"], app.config["PHASE5_IDS"]["se2"]],
        [app.config["PHASE5_IDS"]["delivery1"]],
    )
    response = client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload)
    assert response.status_code == 200
    with app.app_context():
        rows = OpportunityTeam.query.filter_by(opportunity_id=oid).all()
        assert sum(row.role == SOLUTION_ENGINEER for row in rows) == 2
        assert sum(row.role == DELIVERY for row in rows) == 1


def reset_assignment(app):
    with app.app_context():
        oid = app.config["PHASE5_IDS"]["opportunity"]
        opportunity = db.session.get(Opportunity, oid)
        for row in list(opportunity.team_members):
            if row.role in {SOLUTION_ENGINEER, DELIVERY}:
                db.session.delete(row)
        opportunity.status = APPROVED_STATUS
        db.session.commit()


def test_16_duplicate_role_assignment_rejected(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(
        app,
        [app.config["PHASE5_IDS"]["se1"], app.config["PHASE5_IDS"]["se1"]],
        [app.config["PHASE5_IDS"]["delivery1"]],
    )
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_17_no_se_rejected(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_18_no_delivery_rejected(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 400


def test_19_second_finalization_rejected(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 200
    with app.app_context():
        current = db.session.get(Opportunity, oid)
        payload["updated_at"] = current.updated_at.isoformat()
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 409


def test_20_replace_api_does_not_exist(client, app):
    oid = app.config["PHASE5_IDS"]["opportunity"]
    token = token_for(client, "psm5@example.com")
    assert client.put(f"/api/opportunities/{oid}/team", headers=auth(token), json={}).status_code == 404


def test_21_remove_api_does_not_exist(client, app):
    oid = app.config["PHASE5_IDS"]["opportunity"]
    token = token_for(client, "psm5@example.com")
    assert client.delete(f"/api/opportunities/{oid}/team/1", headers=auth(token)).status_code == 404


def test_22_invalid_multi_user_assignment_is_atomic(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(
        app,
        [app.config["PHASE5_IDS"]["se1"], app.config["PHASE5_IDS"]["wrong"]],
        [app.config["PHASE5_IDS"]["delivery1"]],
    )
    response = client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload)
    assert response.status_code == 400
    with app.app_context():
        opportunity = db.session.get(Opportunity, oid)
        assert opportunity.status == APPROVED_STATUS
        assert not OpportunityTeam.query.filter(
            OpportunityTeam.opportunity_id == oid,
            OpportunityTeam.role.in_([SOLUTION_ENGINEER, DELIVERY]),
        ).first()


def test_23_audit_records_are_created(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 200
    with app.app_context():
        actions = {row.action for row in AuditLog.query.filter_by(entity_id=oid, entity_type="Opportunity").all()}
        assert PRE_SALES_ASSIGNMENT_FINALIZED in actions
        assert SOLUTION_ENGINEER_ASSIGNED in actions
        assert DELIVERY_ASSIGNED in actions


def test_24_notifications_are_created(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 200
    with app.app_context():
        assert Notification.query.filter_by(recipient_user_id=app.config["PHASE5_IDS"]["se1"], notification_type=SOLUTION_ENGINEER_ASSIGNED).count() == 1
        assert Notification.query.filter_by(recipient_user_id=app.config["PHASE5_IDS"]["delivery1"], notification_type=DELIVERY_ASSIGNED).count() == 1


def test_25_assigned_se_can_retrieve_opportunity(client, app):
    reset_assignment(app)
    token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 200
    se_token = token_for(client, "se1_5@example.com")
    assert client.get(f"/api/opportunities/{oid}", headers=auth(se_token)).status_code == 200


def test_26_assigned_delivery_can_retrieve_opportunity(client, app):
    reset_assignment(app)
    manager_token = token_for(client, "psm5@example.com")
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(manager_token), json=payload).status_code == 200
    delivery_token = token_for(client, "delivery1_5@example.com")
    assert client.get(f"/api/opportunities/{oid}", headers=auth(delivery_token)).status_code == 200


def test_27_unassigned_se_cannot_retrieve_opportunity(client, app):
    reset_assignment(app)
    token = token_for(client, "se2_5@example.com")
    oid = app.config["PHASE5_IDS"]["opportunity"]
    assert client.get(f"/api/opportunities/{oid}", headers=auth(token)).status_code == 404


def test_28_unassigned_delivery_cannot_retrieve_opportunity(client, app):
    reset_assignment(app)
    token = token_for(client, "delivery2_5@example.com")
    oid = app.config["PHASE5_IDS"]["opportunity"]
    assert client.get(f"/api/opportunities/{oid}", headers=auth(token)).status_code == 404


def test_29_sales_manager_sees_opportunity_but_cannot_modify_team(client, app):
    token = token_for(client, "manager5@example.com")
    oid = app.config["PHASE5_IDS"]["opportunity"]
    assert client.get(f"/api/opportunities/{oid}", headers=auth(token)).status_code == 200
    _, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 403


def test_30_sales_executive_sees_opportunity_but_cannot_modify_team(client, app):
    token = token_for(client, "creator5@example.com")
    oid = app.config["PHASE5_IDS"]["opportunity"]
    assert client.get(f"/api/opportunities/{oid}", headers=auth(token)).status_code == 200
    _, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(token), json=payload).status_code == 403


def test_31_admin_cannot_see_business_opportunity(client, app):
    token = token_for(client, "admin5@example.com")
    oid = app.config["PHASE5_IDS"]["opportunity"]
    assert client.get(f"/api/opportunities/{oid}", headers=auth(token)).status_code == 403


def test_32_active_role_enforcement_for_multi_role_user(client, app):
    session = login(client, "multi_manager_se5@example.com")
    assert session["requires_role_selection"] is True

    selected_se = client.post(
        "/api/auth/select-role",
        json={"role": SOLUTION_ENGINEER},
        headers=auth(session["refresh_token"]),
    )
    assert selected_se.status_code == 200
    se_token = selected_se.get_json()["access_token"]
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(se_token), json=payload).status_code == 403

    selected_manager = client.post(
        "/api/auth/select-role",
        json={"role": PRE_SALES_MANAGER},
        headers=auth(selected_se.get_json()["refresh_token"]),
    )
    assert selected_manager.status_code == 200
    manager_token = selected_manager.get_json()["access_token"]
    reset_assignment(app)
    oid, payload = assignment_payload(app, [app.config["PHASE5_IDS"]["se1"]], [app.config["PHASE5_IDS"]["delivery1"]])
    assert client.post(f"/api/opportunities/{oid}/finalize-pre-sales-assignment", headers=auth(manager_token), json=payload).status_code == 200
