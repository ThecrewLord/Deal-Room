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
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.stakeholder import Stakeholder


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "phase2.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("JWT_SECRET_KEY", "phase2-test-secret")

    from app import create_app

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        stages = [
            StageMaster(stage_name="Lead / Identified", display_order=1, requires_poc=False),
            StageMaster(stage_name="Qualification", display_order=2, requires_poc=False),
            StageMaster(stage_name="Discovery", display_order=3, requires_poc=False),
            StageMaster(stage_name="POC / Technical Evaluation", display_order=4, requires_poc=True),
        ]
        db.session.add_all(stages)
        db.session.flush()

        account_a = Account(account_name="Acme A")
        account_b = Account(account_name="Acme B")
        db.session.add_all([account_a, account_b])
        db.session.flush()

        def make_user(name, role, email, extra_roles=None):
            user = User(
                full_name=name,
                email=email,
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            user.roles.append(UserRole(role=role))
            for extra in extra_roles or []:
                user.roles.append(UserRole(role=extra))
            db.session.add(user)
            db.session.flush()
            return user

        admin = make_user("Admin", ADMIN, "admin@example.com")
        sales_a = make_user("Sales A", SALES_EXECUTIVE, "salesa@example.com")
        sales_b = make_user("Sales B", SALES_EXECUTIVE, "salesb@example.com")
        manager = make_user("Sales Manager", SALES_MANAGER, "sm@example.com")
        presales = make_user("Pre Sales Manager", PRE_SALES_MANAGER, "psm@example.com")
        se_a = make_user("SE A", SOLUTION_ENGINEER, "sea@example.com")
        se_b = make_user("SE B", SOLUTION_ENGINEER, "seb@example.com")
        delivery = make_user("Delivery", DELIVERY, "delivery@example.com")
        multi = make_user(
            "Multi",
            SALES_EXECUTIVE,
            "multi@example.com",
            extra_roles=[SOLUTION_ENGINEER],
        )

        opp_a = Opportunity(
            account_id=account_a.account_id,
            stage_id=stages[2].stage_id,
            opportunity_name="Opportunity A",
            status="Open",
            is_active=True,
        )
        opp_b = Opportunity(
            account_id=account_b.account_id,
            stage_id=stages[2].stage_id,
            opportunity_name="Opportunity B",
            status="Open",
            is_active=True,
        )
        sales_opp = Opportunity(
            account_id=account_a.account_id,
            stage_id=stages[1].stage_id,
            opportunity_name="Sales Scope",
            status="Open",
            is_active=True,
        )
        db.session.add_all([opp_a, opp_b, sales_opp])
        db.session.flush()

        db.session.add_all([
            OpportunityTeam(opportunity_id=opp_a.opportunity_id, user_id=se_a.user_id, role=SOLUTION_ENGINEER),
            OpportunityTeam(opportunity_id=opp_a.opportunity_id, user_id=sales_a.user_id, role=SALES_EXECUTIVE),
            OpportunityTeam(opportunity_id=opp_a.opportunity_id, user_id=delivery.user_id, role=DELIVERY),
            OpportunityTeam(opportunity_id=opp_a.opportunity_id, user_id=multi.user_id, role=SALES_EXECUTIVE),
            OpportunityTeam(opportunity_id=opp_b.opportunity_id, user_id=se_b.user_id, role=SOLUTION_ENGINEER),
            OpportunityTeam(opportunity_id=opp_b.opportunity_id, user_id=sales_b.user_id, role=SALES_EXECUTIVE),
            OpportunityTeam(opportunity_id=sales_opp.opportunity_id, user_id=sales_b.user_id, role=SALES_EXECUTIVE),
        ])

        poc = POCTracker(
            opportunity_id=opp_b.opportunity_id,
            poc_name="B POC",
            objective="B objective",
            success_metric="B metric",
            target_date=__import__("datetime").date.today(),
            failure_condition="B failure",
        )
        stakeholder = Stakeholder(
            opportunity_id=opp_b.opportunity_id,
            stakeholder_name="B Stakeholder",
        )
        db.session.add_all([poc, stakeholder])
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
    data = response.get_json()
    assert data.get("access_token")
    return data["access_token"]


def multi_login(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "multi@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    return response.get_json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_cannot_access_business_dashboard_or_opportunities(client):
    token = login(client, "admin@example.com")
    assert client.get("/api/dashboard", headers=auth(token)).status_code == 403
    assert client.get("/api/opportunities", headers=auth(token)).status_code == 403


def test_sales_executive_isolation_collection_and_direct_id(client, app):
    token = login(client, "salesa@example.com")
    with app.app_context():
        opp_a = Opportunity.query.filter_by(opportunity_name="Opportunity A").first()
        opp_b = Opportunity.query.filter_by(opportunity_name="Opportunity B").first()
        a_id, b_id = opp_a.opportunity_id, opp_b.opportunity_id

    ids = {row["opportunity_id"] for row in client.get("/api/opportunities", headers=auth(token)).get_json()}
    assert a_id in ids
    assert b_id not in ids
    assert client.get(f"/api/opportunities/{a_id}", headers=auth(token)).status_code == 200
    assert client.get(f"/api/opportunities/{b_id}", headers=auth(token)).status_code == 404


def test_sales_manager_has_sales_scope(client, app):
    token = login(client, "sm@example.com")
    with app.app_context():
        sales_id = Opportunity.query.filter_by(opportunity_name="Sales Scope").first().opportunity_id
        technical_id = Opportunity.query.filter_by(opportunity_name="Opportunity A").first().opportunity_id
    ids = {row["opportunity_id"] for row in client.get("/api/opportunities", headers=auth(token)).get_json()}
    assert sales_id in ids
    assert technical_id in ids


def test_pre_sales_manager_has_pre_sales_scope(client, app):
    token = login(client, "psm@example.com")
    with app.app_context():
        discovery_id = Opportunity.query.filter_by(opportunity_name="Opportunity A").first().opportunity_id
        sales_id = Opportunity.query.filter_by(opportunity_name="Sales Scope").first().opportunity_id
    ids = {row["opportunity_id"] for row in client.get("/api/opportunities", headers=auth(token)).get_json()}
    assert discovery_id in ids
    assert sales_id not in ids


def test_solution_engineer_and_delivery_are_participation_scoped(client, app):
    with app.app_context():
        a_id = Opportunity.query.filter_by(opportunity_name="Opportunity A").first().opportunity_id
        b_id = Opportunity.query.filter_by(opportunity_name="Opportunity B").first().opportunity_id

    se_token = login(client, "sea@example.com")
    assert client.get(f"/api/opportunities/{a_id}", headers=auth(se_token)).status_code == 200
    assert client.get(f"/api/opportunities/{b_id}", headers=auth(se_token)).status_code == 404

    delivery_token = login(client, "delivery@example.com")
    assert client.get(f"/api/opportunities/{a_id}", headers=auth(delivery_token)).status_code == 200
    assert client.get(f"/api/opportunities/{b_id}", headers=auth(delivery_token)).status_code == 404


def test_related_account_stakeholder_and_poc_do_not_cross_opportunities(client, app):
    token = login(client, "sea@example.com")
    with app.app_context():
        account_b = Account.query.filter_by(account_name="Acme B").first()
        opp_b = Opportunity.query.filter_by(opportunity_name="Opportunity B").first()
        stakeholder = Stakeholder.query.filter_by(opportunity_id=opp_b.opportunity_id).first()
        poc = POCTracker.query.filter_by(opportunity_id=opp_b.opportunity_id).first()
        account_b_id = account_b.account_id
        opp_b_id = opp_b.opportunity_id
        stakeholder_id = stakeholder.stakeholder_id
        poc_id = poc.poc_id

    assert client.get(f"/api/accounts/{account_b_id}", headers=auth(token)).status_code == 404
    assert client.get(f"/api/stakeholder/{stakeholder_id}", headers=auth(token)).status_code == 404
    assert client.get(f"/api/poc/{poc_id}", headers=auth(token)).status_code == 404
    assert client.get(f"/api/stakeholder/opportunity/{opp_b_id}", headers=auth(token)).get_json() == []
    assert client.get(f"/api/poc/opportunity/{opp_b_id}", headers=auth(token)).get_json() == []


def test_active_role_does_not_merge_permissions(client, app):
    response = multi_login(client)
    refresh = response["refresh_token"]

    sales_selected = client.post(
        "/api/auth/select-role",
        json={"role": SALES_EXECUTIVE},
        headers=auth(refresh),
    )
    assert sales_selected.status_code == 200
    sales_access = sales_selected.get_json()["access_token"]

    with app.app_context():
        sales_id = Opportunity.query.filter_by(opportunity_name="Opportunity A").first().opportunity_id
    assert client.get(f"/api/opportunities/{sales_id}", headers=auth(sales_access)).status_code == 200

    # Select the other assigned role using the newly issued refresh token.
    selected = client.post(
        "/api/auth/select-role",
        json={"role": SOLUTION_ENGINEER},
        headers=auth(sales_selected.get_json()["refresh_token"]),
    )
    assert selected.status_code == 200
    token = selected.get_json()["access_token"]

    with app.app_context():
        opp_a = Opportunity.query.filter_by(opportunity_name="Opportunity A").first()
        opp_b = Opportunity.query.filter_by(opportunity_name="Opportunity B").first()
        a_id, b_id = opp_a.opportunity_id, opp_b.opportunity_id

    assert client.get(f"/api/opportunities/{a_id}", headers=auth(token)).status_code == 404
    assert client.get(f"/api/opportunities/{b_id}", headers=auth(token)).status_code == 404


def test_unauthorized_mutation_returns_403(client, app):
    token = login(client, "sea@example.com")
    with app.app_context():
        opp_a = Opportunity.query.filter_by(opportunity_name="Opportunity A").first()
        poc = POCTracker.query.filter_by(opportunity_id=opp_a.opportunity_id).first()
        # Create an owned POC for the SE's visible opportunity.
        if not poc:
            poc = POCTracker(
                opportunity_id=opp_a.opportunity_id,
                poc_name="A POC",
                objective="A objective",
                success_metric="A metric",
                target_date=__import__("datetime").date.today(),
                failure_condition="A failure",
            )
            db.session.add(poc)
            db.session.commit()
        poc_id = poc.poc_id

    response = client.put(
        f"/api/poc/{poc_id}",
        headers=auth(token),
        json={"status": "In Progress", "updated_at": "2026-08-12T00:00:00"},
    )
    assert response.status_code == 403


def test_unauthenticated_business_access_is_401(client):
    assert client.get("/api/opportunities").status_code == 401
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/accounts").status_code == 401


def test_dashboard_returns_200_for_all_business_roles_and_preserves_admin_denial(client):
    role_emails = [
        "salesa@example.com",
        "sm@example.com",
        "psm@example.com",
        "sea@example.com",
        "delivery@example.com",
    ]
    for email in role_emails:
        token = login(client, email)
        response = client.get("/api/dashboard", headers=auth(token))
        assert response.status_code == 200, response.get_json()
        payload = response.get_json()
        assert "total_opportunities" in payload
        assert "pipeline_by_stage" in payload
        assert "recent_opportunities" in payload

    admin_token = login(client, "admin@example.com")
    assert client.get("/api/dashboard", headers=auth(admin_token)).status_code == 403


def test_dashboard_role_visibility_does_not_cross_business_scopes(client, app):
    with app.app_context():
        opp_a = Opportunity.query.filter_by(opportunity_name="Opportunity A").first()
        opp_b = Opportunity.query.filter_by(opportunity_name="Opportunity B").first()
        sales_scope = Opportunity.query.filter_by(opportunity_name="Sales Scope").first()
        a_id, b_id, sales_id = opp_a.opportunity_id, opp_b.opportunity_id, sales_scope.opportunity_id

    sales_token = login(client, "salesa@example.com")
    sales_payload = client.get("/api/dashboard", headers=auth(sales_token)).get_json()
    sales_ids = {row["id"] for row in sales_payload["recent_opportunities"]}

    se_token = login(client, "sea@example.com")
    se_payload = client.get("/api/dashboard", headers=auth(se_token)).get_json()
    se_ids = {row["id"] for row in se_payload["recent_opportunities"]}

    assert a_id in sales_ids
    assert b_id not in sales_ids
    assert sales_id not in se_ids
    assert b_id not in se_ids
