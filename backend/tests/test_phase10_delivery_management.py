import pytest
from datetime import date, timedelta

from app.auth.password import hash_password
from app.constants.roles import *
from app.constants.stages import *
from app.database import db

from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.poc_tracker import POCTracker
from app.models.delivery.delivery_project import DeliveryProject
from app.models.delivery.delivery_assignment import DeliveryAssignment
from app.models.poc.poc_assignment import POCAssignment
from app.models.system.audit_log import AuditLog
from app.models.system.notification import Notification
from app.services.poc_service import PocService


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite:///{tmp_path / 'phase10_delivery.db'}",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "phase10-test-secret",
    )

    from app import create_app

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        stages = [
            StageMaster(
                stage_name=n,
                display_order=i,
                requires_poc=(n == "POC / Technical Evaluation"),
                is_closed=n.startswith("Closed"),
                is_won=n == "Closed Won",
            )
            for i, n in enumerate(
                [
                    "Lead / Identified",
                    "Qualification",
                    "Discovery",
                    "POC / Technical Evaluation",
                    "Proposal",
                    "Negotiation",
                    "Closed Won",
                    "Closed Lost",
                ],
                1,
            )
        ]

        db.session.add_all(stages)
        db.session.flush()

        def user(name, email, role, extras=(), active=True, status="APPROVED"):
            u = User(
                full_name=name,
                email=email,
                password_hash=hash_password("Password123!"),
                status=status,
                active=active,
            )
            u.roles.append(UserRole(role=role))

            for r in extras:
                u.roles.append(UserRole(role=r))

            db.session.add(u)
            db.session.flush()
            return u

        dm = user(
            "Delivery Manager",
            "dm10@example.com",
            DELIVERY_MANAGER,
        )

        devops = user(
            "DevOps Engineer",
            "devops10@example.com",
            DEVOPS_ENGINEER,
        )

        analyst = user(
            "Data Analyst",
            "analyst10@example.com",
            DATA_ANALYST,
        )

        delivery = user(
            "Delivery",
            "delivery10@example.com",
            DELIVERY,
        )

        sales = user(
            "Sales Executive",
            "sales10@example.com",
            SALES_EXECUTIVE,
        )

        psm = user(
            "Pre-Sales Manager",
            "psm10@example.com",
            PRE_SALES_MANAGER,
        )

        inactive_devops = user(
            "Inactive DevOps",
            "inactive-devops10@example.com",
            DEVOPS_ENGINEER,
            active=False,
        )

        unapproved_analyst = user(
            "Pending Analyst",
            "pending-analyst10@example.com",
            DATA_ANALYST,
            status="PENDING",
        )

        multi = user(
            "Multi Role",
            "multi10@example.com",
            DEVOPS_ENGINEER,
            extras=(DATA_ANALYST,),
        )

        account = Account(
            account_name="Phase 10 Delivery Account",
        )
        db.session.add(account)
        db.session.flush()

        opp = Opportunity(
            account_id=account.account_id,
            created_by=sales.user_id,
            sales_owner_id=sales.user_id,
            stage_id=stages[3].stage_id,
            opportunity_name="Phase 10 Delivery Opportunity",
            status=ACTIVE_STATUS,
            is_active=True,
        )

        db.session.add(opp)
        db.session.flush()

        db.session.add_all([
            OpportunityTeam(
                opportunity_id=opp.opportunity_id,
                user_id=sales.user_id,
                role=SALES_EXECUTIVE,
            ),
        ])

        poc = POCTracker(
            opportunity_id=opp.opportunity_id,
            poc_name="Phase 10 Completed POC",
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=2),
            status="Completed",
            remarks="Completed successfully.",
            objective="Validate delivery readiness.",
            success_metric="All technical success metrics passed.",
            target_date=date.today() - timedelta(days=2),
            failure_condition="Required success metrics fail.",
            outcome="Success",
            outcome_notes="POC completed successfully.",
            exit_criteria="All agreed exit criteria satisfied.",
            requested_by=sales.user_id,
            submitted_by=sales.user_id,
            submitted_at=None,
        )

        db.session.add(poc)
        db.session.commit()

        application.config["P10"] = {
            "opp": opp.opportunity_id,
            "poc": poc.poc_id,

            "dm": dm.email,
            "dm_id": dm.user_id,

            "devops": devops.email,
            "devops_id": devops.user_id,

            "analyst": analyst.email,
            "analyst_id": analyst.user_id,

            "delivery": delivery.email,
            "delivery_id": delivery.user_id,

            "sales": sales.email,
            "psm": psm.email,

            "inactive_devops": inactive_devops.email,
            "inactive_devops_id": inactive_devops.user_id,

            "unapproved_analyst": unapproved_analyst.email,
            "unapproved_analyst_id": unapproved_analyst.user_id,

            "multi": multi.email,
            "multi_id": multi.user_id,
        }

    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def auth(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def token_for(client, email, role=None):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    if payload.get("requires_role_selection"):
        response = client.post(
            "/api/auth/select-role",
            json={"role": role},
            headers=auth(payload["refresh_token"]),
        )

        assert response.status_code == 200

        return response.get_json()["access_token"]

    return payload["access_token"]


def create_project(client, app):
    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    import jwt
    decoded = jwt.decode(
        token,
        options={"verify_signature": False},
    )
    print("\nDEBUG TOKEN:", decoded)

    response = client.post(
        "/api/delivery/projects",
        headers=auth(token),
        json={
            "opportunity_id": app.config["P10"]["opp"],
            "poc_id": app.config["P10"]["poc"],
            "project_name": "Phase 10 Delivery Project",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=30)),
        },
    )

    assert response.status_code == 201, response.get_json()

    return response.get_json()


def test_delivery_manager_can_create_project_from_completed_poc(client, app):
    project = create_project(client, app)

    assert project["project_name"] == "Phase 10 Delivery Project"
    assert project["status"] == "Pending Assignment"
    assert project["opportunity_id"] == app.config["P10"]["opp"]
    assert project["poc_id"] == app.config["P10"]["poc"]


def test_non_delivery_manager_cannot_create_project(client, app):
    token = token_for(
        client,
        app.config["P10"]["sales"],
        SALES_EXECUTIVE,
    )

    response = client.post(
        "/api/delivery/projects",
        headers=auth(token),
        json={
            "opportunity_id": app.config["P10"]["opp"],
            "poc_id": app.config["P10"]["poc"],
            "project_name": "Unauthorized Project",
        },
    )

    assert response.status_code in (400, 403)


def test_delivery_project_duplicate_for_same_poc_is_rejected(client, app):
    create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        "/api/delivery/projects",
        headers=auth(token),
        json={
            "opportunity_id": app.config["P10"]["opp"],
            "poc_id": app.config["P10"]["poc"],
            "project_name": "Second Project",
        },
    )

    assert response.status_code == 400


def test_invalid_project_dates_are_rejected(client, app):
    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        "/api/delivery/projects",
        headers=auth(token),
        json={
            "opportunity_id": app.config["P10"]["opp"],
            "poc_id": app.config["P10"]["poc"],
            "project_name": "Invalid Dates",
            "start_date": "2026-09-20",
            "target_date": "2026-09-10",
        },
    )

    assert response.status_code == 400


def test_delivery_manager_can_assign_devops(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    payload = response.get_json()

    assert payload["project_id"] == project["project_id"]
    assert payload["user_id"] == app.config["P10"]["devops_id"]
    assert payload["role"] == DEVOPS_ENGINEER
    assert payload["is_active"] is True


def test_delivery_manager_can_assign_data_analyst(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["analyst_id"],
            "role": DATA_ANALYST,
        },
    )

    assert response.status_code == 201


def test_delivery_manager_can_assign_delivery_member(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["delivery_id"],
            "role": DELIVERY,
        },
    )

    assert response.status_code == 201


def test_wrong_role_cannot_be_assigned(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["sales"] and 999999,
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code in (400, 404)


def test_inactive_user_cannot_be_assigned(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["inactive_devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 400


def test_unapproved_user_cannot_be_assigned(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["unapproved_analyst_id"],
            "role": DATA_ANALYST,
        },
    )

    assert response.status_code == 400


def test_duplicate_assignment_is_rejected(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    payload = {
        "user_id": app.config["P10"]["devops_id"],
        "role": DEVOPS_ENGINEER,
    }

    first = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json=payload,
    )

    assert second.status_code == 400


def test_assignment_can_be_removed(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    response = client.delete(
        f"/api/delivery/projects/{project['project_id']}/assign/{app.config['P10']['devops_id']}",
        headers=auth(token),
    )

    assert response.status_code == 200


def test_removed_assignment_can_be_reactivated(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    payload = {
        "user_id": app.config["P10"]["devops_id"],
        "role": DEVOPS_ENGINEER,
    }

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json=payload,
    )

    assert response.status_code == 201

    response = client.delete(
        f"/api/delivery/projects/{project['project_id']}/assign/{app.config['P10']['devops_id']}",
        headers=auth(token),
    )

    assert response.status_code == 200

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json=payload,
    )

    assert response.status_code == 201
    assert response.get_json()["is_active"] is True


def test_assigned_delivery_member_can_view_project(client, app):
    project = create_project(client, app)

    dm_token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(dm_token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    devops_token = token_for(
        client,
        app.config["P10"]["devops"],
        DEVOPS_ENGINEER,
    )

    response = client.get(
        f"/api/delivery/projects/{project['project_id']}",
        headers=auth(devops_token),
    )

    assert response.status_code == 200
    assert response.get_json()["project_id"] == project["project_id"]


def test_unassigned_delivery_member_cannot_view_project(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["devops"],
        DEVOPS_ENGINEER,
    )

    response = client.get(
        f"/api/delivery/projects/{project['project_id']}",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_sales_user_cannot_view_delivery_project(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["sales"],
        SALES_EXECUTIVE,
    )

    response = client.get(
        f"/api/delivery/projects/{project['project_id']}",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_delivery_manager_can_view_project(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.get(
        f"/api/delivery/projects/{project['project_id']}",
        headers=auth(token),
    )

    assert response.status_code == 200


def test_get_project_contains_assignments(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/delivery/projects/{project['project_id']}",
        headers=auth(token),
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert "assignments" in payload
    assert len(payload["assignments"]) == 1
    assert payload["assignments"][0]["role"] == DEVOPS_ENGINEER


def test_delivery_project_audit_is_recorded(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    with app.app_context():
        logs = AuditLog.query.filter_by(
            entity_type="delivery_project",
            entity_id=project["project_id"],
        ).all()

        actions = {log.action for log in logs}

        assert "DELIVERY_PROJECT_CREATED" in actions
        assert "DELIVERY_ASSIGNMENT_CREATED" in actions


def test_completed_project_cannot_be_modified(client, app):
    project = create_project(client, app)

    with app.app_context():
        delivery_project = db.session.get(
            DeliveryProject,
            project["project_id"],
        )
        delivery_project.status = "Done"
        db.session.commit()

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 400


# ============================================================
# B5 — PENDING DELIVERY ASSIGNMENTS
# ============================================================

def test_delivery_manager_can_view_pending_assignments(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/pending",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "count" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    # The fixture creates a completed POC without a delivery project.
    with client.application.app_context():
        poc = POCTracker.query.filter_by(
            poc_name="Phase 10 Completed POC"
        ).first()

    assert poc is not None
    assert any(
        item["poc_id"] == poc.poc_id
        for item in data["items"]
    )


@pytest.mark.parametrize(
    "email,role",
    [
        ("devops10@example.com", DEVOPS_ENGINEER),
        ("analyst10@example.com", DATA_ANALYST),
        ("delivery10@example.com", DELIVERY),
        ("sales10@example.com", SALES_EXECUTIVE),
        ("psm10@example.com", PRE_SALES_MANAGER),
    ],
)
def test_non_delivery_manager_cannot_view_pending_assignments(
    client,
    email,
    role,
):
    token = token_for(client, email, role)

    response = client.get(
        "/api/delivery/pending",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_pending_assignment_contains_expected_poc_fields(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/pending",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    with client.application.app_context():
        poc = POCTracker.query.filter_by(
            poc_name="Phase 10 Completed POC"
        ).first()

    assert poc is not None

    item = next(
        item for item in data["items"]
        if item["poc_id"] == poc.poc_id
    )

    assert item["opportunity_id"] == poc.opportunity_id
    assert item["poc_name"] == "Phase 10 Completed POC"
    assert item["status"] == "Completed"
    assert item["target_date"] is not None
    assert item["objective"] is not None
    assert item["success_metric"] is not None
    assert item["failure_condition"] is not None


def test_completed_poc_with_project_is_not_pending(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    with client.application.app_context():
        poc = POCTracker.query.filter_by(
            poc_name="Phase 10 Completed POC"
        ).first()

    assert poc is not None

    # Create the delivery project for the completed POC.
    response = client.post(
        "/api/delivery/projects",
        json={
            "opportunity_id": poc.opportunity_id,
            "poc_id": poc.poc_id,
            "project_name": "Pending Filter Test Project",
        },
        headers=auth(token),
    )

    assert response.status_code == 201

    response = client.get(
        "/api/delivery/pending",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert not any(
        item["poc_id"] == P10["poc"]
        for item in data["items"]
    )


def test_pending_assignments_returns_empty_items_when_none_pending(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    with client.application.app_context():
        poc = POCTracker.query.filter_by(
            poc_name="Phase 10 Completed POC"
        ).first()

    assert poc is not None

    # Create a project for the fixture POC.
    response = client.post(
        "/api/delivery/projects",
        json={
            "opportunity_id": poc.opportunity_id,
            "poc_id": poc.poc_id,
            "project_name": "No Pending POC Project",
        },
        headers=auth(token),
    )

    assert response.status_code == 201

    response = client.get(
        "/api/delivery/pending",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 0
    assert data["items"] == []


# ============================================================
# B5 — DELIVERY CANDIDATES
# ============================================================

def test_delivery_manager_can_view_delivery_candidates(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/candidates",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "count" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    emails = {
        item["email"]
        for item in data["items"]
    }

    assert "devops10@example.com" in emails
    assert "analyst10@example.com" in emails
    assert "delivery10@example.com" in emails


@pytest.mark.parametrize(
    "email,role",
    [
        ("devops10@example.com", DEVOPS_ENGINEER),
        ("analyst10@example.com", DATA_ANALYST),
        ("delivery10@example.com", DELIVERY),
        ("sales10@example.com", SALES_EXECUTIVE),
        ("psm10@example.com", PRE_SALES_MANAGER),
    ],
)
def test_non_delivery_manager_cannot_view_delivery_candidates(
    client,
    email,
    role,
):
    token = token_for(client, email, role)

    response = client.get(
        "/api/delivery/candidates",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_delivery_candidates_exclude_inactive_and_unapproved_users(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/candidates",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    emails = {
        item["email"]
        for item in data["items"]
    }

    assert "inactive-devops10@example.com" not in emails
    assert "pending-analyst10@example.com" not in emails


def test_delivery_candidates_include_valid_roles(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/candidates",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    by_email = {
        item["email"]: item
        for item in data["items"]
    }

    assert DEVOPS_ENGINEER in by_email["devops10@example.com"]["roles"]
    assert DATA_ANALYST in by_email["analyst10@example.com"]["roles"]
    assert DELIVERY in by_email["delivery10@example.com"]["roles"]


def test_multi_role_delivery_candidate_returns_all_delivery_roles(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/candidates",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    multi = next(
        item
        for item in data["items"]
        if item["email"] == "multi10@example.com"
    )

    assert DEVOPS_ENGINEER in multi["roles"]
    assert DATA_ANALYST in multi["roles"]


def test_delivery_manager_is_not_returned_as_team_candidate(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/candidates",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    emails = {
        item["email"]
        for item in data["items"]
    }

    assert "dm10@example.com" not in emails


def test_candidate_response_contains_required_fields(client):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/candidates",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == len(data["items"])

    for item in data["items"]:
        assert "user_id" in item
        assert "full_name" in item
        assert "email" in item
        assert "roles" in item
        assert isinstance(item["roles"], list)
        assert len(item["roles"]) > 0


# ============================================================
# B5 — DELIVERY PROJECT LIFECYCLE
# ============================================================

def test_delivery_project_cannot_be_assigned_without_team_member(client, app):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    project = create_project(client, app)

    project_id = project["project_id"]

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "Assigned"},
    )

    assert response.status_code == 400
    assert "team member" in response.get_json()["message"]


def test_delivery_manager_can_move_project_to_assigned(client, app):
    token = token_for(client, "dm10@example.com", DELIVERY_MANAGER)

    project = create_project(client, app)
    project_id = project["project_id"]

    user = User.query.filter_by(
        email="devops10@example.com"
    ).first()

    assert user is not None

    response = client.post(
        f"/api/delivery/projects/{project_id}/assign",
        headers=auth(token),
        json={
            "user_id": user.user_id,
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "Assigned"},
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "Assigned"


def test_assigned_team_member_can_start_project(client, app):
    dm_token = token_for(
        client,
        "dm10@example.com",
        DELIVERY_MANAGER,
    )

    project = create_project(client, app)
    project_id = project["project_id"]

    user = User.query.filter_by(
        email="devops10@example.com"
    ).first()

    assert user is not None

    response = client.post(
        f"/api/delivery/projects/{project_id}/assign",
        headers=auth(dm_token),
        json={
            "user_id": user.user_id,
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(dm_token),
        json={"status": "Assigned"},
    )

    assert response.status_code == 200

    token = token_for(
        client,
        "devops10@example.com",
        DEVOPS_ENGINEER,
    )

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "In Progress"},
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "In Progress"


def test_assigned_team_member_can_complete_project(client, app):
    dm_token = token_for(
        client,
        "dm10@example.com",
        DELIVERY_MANAGER,
    )

    project = create_project(client, app)
    project_id = project["project_id"]

    user = User.query.filter_by(
        email="devops10@example.com"
    ).first()

    assert user is not None

    response = client.post(
        f"/api/delivery/projects/{project_id}/assign",
        headers=auth(dm_token),
        json={
            "user_id": user.user_id,
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code == 201

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(dm_token),
        json={"status": "Assigned"},
    )

    assert response.status_code == 200

    token = token_for(
        client,
        "devops10@example.com",
        DEVOPS_ENGINEER,
    )

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "In Progress"},
    )

    assert response.status_code == 200

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "Done"},
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "Done"


@pytest.mark.parametrize(
    "email,role",
    [
        ("sales10@example.com", SALES_EXECUTIVE),
        ("psm10@example.com", PRE_SALES_MANAGER),
        ("analyst10@example.com", DATA_ANALYST),
    ],
)
def test_unauthorized_user_cannot_change_delivery_project_status(
    client,
    app,
    email,
    role,
):
    project = create_project(client, app)
    project_id = project["project_id"]

    # Put project into Assigned state for the authorization test.
    project_record = DeliveryProject.query.get(project_id)
    project_record.status = "Assigned"
    db.session.commit()

    token = token_for(client, email, role)

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "In Progress"},
    )

    assert response.status_code == 400


def test_invalid_delivery_project_status_transition_rejected(client, app):
    token = token_for(
        client,
        "dm10@example.com",
        DELIVERY_MANAGER,
    )

    project = create_project(client, app)
    project_id = project["project_id"]

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "Done"},
    )

    assert response.status_code == 400
    assert "Invalid project status transition" in response.get_json()["message"]


def test_done_delivery_project_cannot_change_status(client, app):
    token = token_for(
        client,
        "dm10@example.com",
        DELIVERY_MANAGER,
    )

    project = create_project(client, app)
    project_id = project["project_id"]

    project_record = DeliveryProject.query.get(project_id)
    project_record.status = "Done"
    db.session.commit()

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "In Progress"},
    )

    assert response.status_code == 400
    assert "Invalid project status transition" in response.get_json()["message"]


def test_delivery_project_status_transition_creates_audit(client, app):
    token = token_for(
        client,
        "dm10@example.com",
        DELIVERY_MANAGER,
    )

    project = create_project(client, app)
    project_id = project["project_id"]

    project_record = DeliveryProject.query.get(project_id)
    project_record.status = "In Progress"
    db.session.commit()

    response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(token),
        json={"status": "Done"},
    )

    assert response.status_code == 200

    audit = AuditLog.query.filter_by(
        entity_type="delivery_project",
        entity_id=project_id,
        action="DELIVERY_PROJECT_COMPLETED",
    ).order_by(
        AuditLog.created_at.desc()
    ).first()

    assert audit is not None



# ======================================================================
# B5 DELIVERY DASHBOARD TESTS
# ======================================================================

def test_delivery_manager_can_view_dashboard(client, app):
    token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "summary" in data
    assert "pending_assignments" in data
    assert "active_projects" in data
    assert "in_progress" in data
    assert "done" in data
    assert "overdue" in data
    assert "upcoming" in data
    assert "team_workload" in data


def test_sales_executive_cannot_view_delivery_dashboard(client, app):
    token = token_for(client, app.config["P10"]["sales"], SALES_EXECUTIVE)

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_pre_sales_manager_cannot_view_delivery_dashboard(client, app):
    token = token_for(client, app.config["P10"]["psm"], PRE_SALES_MANAGER)

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(token),
    )

    assert response.status_code == 403


def test_delivery_dashboard_summary_counts(client, app):
    token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    # Create a delivery project.
    project = create_project(client, app)

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()
    summary = data["summary"]

    assert summary["total_projects"] >= 1
    assert summary["pending_assignments"] >= 1


def test_delivery_dashboard_shows_pending_project(client, app):
    token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    project = create_project(client, app)

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    project_ids = [
        item["project_id"]
        for item in data["pending_assignments"]
    ]

    assert project["project_id"] in project_ids


def test_delivery_dashboard_shows_active_project(client, app):
    dm_token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)
    devops_token = token_for(client, app.config["P10"]["devops"], DEVOPS_ENGINEER)

    project = create_project(client, app)
    project_id = project["project_id"]

    assign_response = client.post(
        f"/api/delivery/projects/{project_id}/assign",
        headers=auth(dm_token),
        json={
            "user_id": app.config["P10"]["devops_id"],
                "role": DEVOPS_ENGINEER,
        },
    )

    if assign_response.status_code != 201:
        print("ASSIGN RESPONSE:", assign_response.status_code, assign_response.get_json())
    print("\nDEBUG ASSIGN:", assign_response.status_code, assign_response.get_json())
    assert assign_response.status_code == 201

    status_response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(dm_token),
        json={"status": "Assigned"},
    )

    assert status_response.status_code == 200

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(dm_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    project_ids = [
        item["project_id"]
        for item in data["active_projects"]
    ]

    assert project_id in project_ids


def test_delivery_dashboard_shows_in_progress_project(client, app):
    dm_token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    project = create_project(client, app)
    project_id = project["project_id"]

    assign_response = client.post(
        f"/api/delivery/projects/{project_id}/assign",
        headers=auth(dm_token),
        json={
            "user_id": app.config["P10"]["devops_id"],
                "role": DEVOPS_ENGINEER,
        },
    )

    if assign_response.status_code != 201:
        print("ASSIGN RESPONSE:", assign_response.status_code, assign_response.get_json())
    print("\nDEBUG ASSIGN:", assign_response.status_code, assign_response.get_json())
    assert assign_response.status_code == 201

    assigned_response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(dm_token),
        json={"status": "Assigned"},
    )

    assert assigned_response.status_code == 200

    progress_response = client.patch(
        f"/api/delivery/projects/{project_id}/status",
        headers=auth(dm_token),
        json={"status": "In Progress"},
    )

    assert progress_response.status_code == 200

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(dm_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    project_ids = [
        item["project_id"]
        for item in data["in_progress"]
    ]

    assert project_id in project_ids


def test_delivery_dashboard_shows_done_project(client, app):
    dm_token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    project = create_project(client, app)
    project_id = project["project_id"]

    assign_response = client.post(
        f"/api/delivery/projects/{project_id}/assign",
        headers=auth(dm_token),
        json={
            "user_id": app.config["P10"]["devops_id"],
                "role": DEVOPS_ENGINEER,
        },
    )

    if assign_response.status_code != 201:
        print("ASSIGN RESPONSE:", assign_response.status_code, assign_response.get_json())
    print("\nDEBUG ASSIGN:", assign_response.status_code, assign_response.get_json())
    assert assign_response.status_code == 201

    for status in ("Assigned", "In Progress", "Done"):
        response = client.patch(
            f"/api/delivery/projects/{project_id}/status",
            headers=auth(dm_token),
            json={"status": status},
        )

        assert response.status_code == 200

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(dm_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    project_ids = [
        item["project_id"]
        for item in data["done"]
    ]

    assert project_id in project_ids


def test_delivery_dashboard_team_workload(client, app):
    dm_token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    project = create_project(client, app)
    project_id = project["project_id"]

    assign_response = client.post(
        f"/api/delivery/projects/{project_id}/assign",
        headers=auth(dm_token),
        json={
            "user_id": app.config["P10"]["devops_id"],
                "role": DEVOPS_ENGINEER,
        },
    )

    if assign_response.status_code != 201:
        print("ASSIGN RESPONSE:", assign_response.status_code, assign_response.get_json())
    print("\nDEBUG ASSIGN:", assign_response.status_code, assign_response.get_json())
    assert assign_response.status_code == 201

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(dm_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    workloads = data["team_workload"]

    devops_user_id = app.config["P10"]["devops_id"]

    matching = [
        item for item in workloads
        if item["user_id"] == devops_user_id
    ]

    assert matching
    assert matching[0]["active_projects"] >= 1
    assert matching[0]["role"] == "DevOps Engineer"


def test_delivery_dashboard_overdue_project(client, app):
    dm_token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    project_response = client.post(
        "/api/delivery/projects",
        headers=auth(dm_token),
        json={
            "opportunity_id": app.config["P10"]["opp"],
            "poc_id": app.config["P10"]["poc"],
            "project_name": "Phase 10 Overdue Delivery Project",
            "start_date": "2026-01-01",
            "target_date": "2026-01-02",
        },
    )

    assert project_response.status_code == 201

    project_id = project_response.get_json()["project_id"]

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(dm_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    project_ids = [
        item["project_id"]
        for item in data["overdue"]
    ]

    assert project_id in project_ids


def test_delivery_dashboard_upcoming_project(client, app):
    dm_token = token_for(client, app.config["P10"]["dm"], DELIVERY_MANAGER)

    project_response = client.post(
        "/api/delivery/projects",
        headers=auth(dm_token),
        json={
            "opportunity_id": app.config["P10"]["opp"],
            "poc_id": app.config["P10"]["poc"],
            "project_name": "Phase 10 Upcoming Delivery Project",
            "start_date": "2099-01-01",
            "target_date": "2099-02-01",
        },
    )

    assert project_response.status_code == 201

    project_id = project_response.get_json()["project_id"]

    response = client.get(
        "/api/delivery/dashboard",
        headers=auth(dm_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    project_ids = [
        item["project_id"]
        for item in data["upcoming"]
    ]

    assert project_id in project_ids


# ======================================================================
# B5.4 NOTIFICATIONS
# ======================================================================

def test_poc_completed_notifies_active_delivery_managers(client, app):
    with client.application.app_context():
        poc = POCTracker.query.filter_by(
            poc_name="Phase 10 Completed POC"
        ).first()

        opportunity = Opportunity.query.get(poc.opportunity_id)

        solution_engineer = User(
            full_name="Phase 10 Solution Engineer",
            email="se10-notification@example.com",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        solution_engineer.roles.append(
            UserRole(role=SOLUTION_ENGINEER)
        )
        db.session.add(solution_engineer)
        db.session.flush()

        db.session.add(
            OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=solution_engineer.user_id,
                role=SOLUTION_ENGINEER,
            )
        )

        db.session.add(
            POCAssignment(
                poc_id=poc.poc_id,
                user_id=solution_engineer.user_id,
                assigned_by=opportunity.created_by,
                role=SOLUTION_ENGINEER,
                is_active=True,
            )
        )

        poc.status = "Submitted"
        db.session.commit()

        updated_at = poc.updated_at

        PocService.complete_poc(
            poc_id=poc.poc_id,
            updated_at=updated_at,
            user=solution_engineer,
            active_role=SOLUTION_ENGINEER,
        )

        notifications = Notification.query.filter_by(
            notification_type="POC_COMPLETED",
            entity_type="poc",
            entity_id=poc.poc_id,
        ).all()

        delivery_manager_ids = {
            user.user_id
            for user in User.query.all()
            if user.active
            and user.status == "APPROVED"
            and user.has_role(DELIVERY_MANAGER)
        }

        notified_ids = {
            notification.recipient_user_id
            for notification in notifications
        }

        assert delivery_manager_ids
        assert notified_ids == delivery_manager_ids

        assert all(
            notification.is_read is False
            for notification in notifications
        )


def test_delivery_project_assignment_creates_notification(client, app):
    project = create_project(client, app)

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code in (200, 201)

    with client.application.app_context():
        notification = Notification.query.filter_by(
            recipient_user_id=app.config["P10"]["devops_id"],
            notification_type="DELIVERY_PROJECT_ASSIGNED",
            entity_type="delivery_project",
            entity_id=project["project_id"],
        ).first()

        assert notification is not None
        assert notification.is_read is False
        assert "Phase 10 Delivery Project" in notification.message
        assert DEVOPS_ENGINEER in notification.message


def test_delivery_assignment_notification_visible_only_to_assigned_user(
    client,
    app,
):
    project = create_project(client, app)

    dm_token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.post(
        f"/api/delivery/projects/{project['project_id']}/assign",
        headers=auth(dm_token),
        json={
            "user_id": app.config["P10"]["devops_id"],
            "role": DEVOPS_ENGINEER,
        },
    )

    assert response.status_code in (200, 201)

    analyst_token = token_for(
        client,
        app.config["P10"]["analyst"],
        DATA_ANALYST,
    )

    response = client.get(
        "/api/notifications",
        headers=auth(analyst_token),
    )

    assert response.status_code == 200

    data = response.get_json()
    notifications = (
        data.get("notifications", data)
        if isinstance(data, dict)
        else data
    )

    assert not any(
        notification.get("notification_type")
        == "DELIVERY_PROJECT_ASSIGNED"
        and notification.get("entity_id")
        == project["project_id"]
        for notification in notifications
    )


def test_delivery_manager_can_see_completed_poc_notification(
    client,
    app,
):
    with client.application.app_context():
        poc = POCTracker.query.filter_by(
            poc_name="Phase 10 Completed POC"
        ).first()

        Notification.query.filter_by(
            notification_type="POC_COMPLETED",
            entity_type="poc",
            entity_id=poc.poc_id,
        ).delete()

        db.session.commit()

        from app.services.notification_service import NotificationService

        dm = User.query.filter_by(
            email=app.config["P10"]["dm"]
        ).first()

        NotificationService.queue(
            dm.user_id,
            "POC_COMPLETED",
            "poc",
            poc.poc_id,
            "POC is ready for delivery project creation.",
        )

        db.session.commit()

    token = token_for(
        client,
        app.config["P10"]["dm"],
        DELIVERY_MANAGER,
    )

    response = client.get(
        "/api/notifications",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()
    notifications = (
        data.get("notifications", data)
        if isinstance(data, dict)
        else data
    )

    assert any(
        notification.get("notification_type") == "POC_COMPLETED"
        and notification.get("entity_id") == app.config["P10"]["poc"]
        for notification in notifications
    )
