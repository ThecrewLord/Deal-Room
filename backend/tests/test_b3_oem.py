import pytest

from app.auth.password import hash_password
from app.constants.roles import (
    DELIVERY,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
)
from app.constants.stages import OPEN_STATUS
from app.database import db
from app.models.account.account import Account
from app.models.account.oem_partner import OEMPartner
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_oem import OpportunityOEM
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "b3_oem.db"

    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite:///{db_path}",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "b3-oem-test-secret",
    )

    from app import create_app

    application = create_app()
    application.config.update(TESTING=True)

    with application.app_context():
        db.drop_all()
        db.create_all()

        stages = [
            StageMaster(
                stage_name="Lead / Identified",
                display_order=1,
                requires_poc=False,
            ),
            StageMaster(
                stage_name="Qualification",
                display_order=2,
                requires_poc=False,
            ),
            StageMaster(
                stage_name="Discovery",
                display_order=3,
                requires_poc=False,
            ),
            StageMaster(
                stage_name="POC / Technical Evaluation",
                display_order=4,
                requires_poc=True,
            ),
        ]

        db.session.add_all(stages)
        db.session.flush()

        def make_user(
            name,
            role,
            email,
            extra_roles=None,
        ):
            user = User(
                full_name=name,
                email=email,
                password_hash=hash_password(
                    "Password123!"
                ),
                status="APPROVED",
                active=True,
            )

            user.roles.append(
                UserRole(role=role)
            )

            for extra in extra_roles or []:
                user.roles.append(
                    UserRole(role=extra)
                )

            db.session.add(user)
            db.session.flush()

            return user

        sales = make_user(
            "Sales Executive",
            SALES_EXECUTIVE,
            "sales@example.com",
        )

        manager = make_user(
            "Sales Manager",
            SALES_MANAGER,
            "sm@example.com",
        )

        presales = make_user(
            "Pre Sales Manager",
            PRE_SALES_MANAGER,
            "psm@example.com",
        )

        se = make_user(
            "Solution Engineer",
            SOLUTION_ENGINEER,
            "se@example.com",
        )

        delivery = make_user(
            "Delivery",
            DELIVERY,
            "delivery@example.com",
        )

        account_a = Account(
            account_name="B3 Account A",
        )

        account_b = Account(
            account_name="B3 Account B",
        )

        db.session.add_all([
            account_a,
            account_b,
        ])
        db.session.flush()

        opportunity_a = Opportunity(
            account_id=account_a.account_id,
            created_by=sales.user_id,
            stage_id=stages[0].stage_id,
            opportunity_name="B3 Opportunity A",
            status=OPEN_STATUS,
            is_active=True,
        )

        opportunity_b = Opportunity(
            account_id=account_a.account_id,
            created_by=sales.user_id,
            stage_id=stages[0].stage_id,
            opportunity_name="B3 Opportunity B",
            status=OPEN_STATUS,
            is_active=True,
        )

        opportunity_other_account = Opportunity(
            account_id=account_b.account_id,
            created_by=sales.user_id,
            stage_id=stages[0].stage_id,
            opportunity_name="B3 Other Account Opportunity",
            status=OPEN_STATUS,
            is_active=True,
        )

        db.session.add_all([
            opportunity_a,
            opportunity_b,
            opportunity_other_account,
        ])
        db.session.flush()

        db.session.add_all([
            OpportunityTeam(
                opportunity_id=opportunity_a.opportunity_id,
                user_id=sales.user_id,
                role=SALES_EXECUTIVE,
            ),
            OpportunityTeam(
                opportunity_id=opportunity_a.opportunity_id,
                user_id=se.user_id,
                role=SOLUTION_ENGINEER,
            ),
            OpportunityTeam(
                opportunity_id=opportunity_a.opportunity_id,
                user_id=delivery.user_id,
                role=DELIVERY,
            ),
            OpportunityTeam(
                opportunity_id=opportunity_b.opportunity_id,
                user_id=sales.user_id,
                role=SALES_EXECUTIVE,
            ),
        ])

        oem_one = OEMPartner(
            account_id=account_a.account_id,
            partner_name="Cisco",
            product_name="Cisco Networking",
            contact_person="Cisco Contact",
            email="cisco@example.com",
            phone="1111111111",
            status="Active",
            notes="Primary networking OEM",
        )

        oem_two = OEMPartner(
            account_id=account_a.account_id,
            partner_name="Dell",
            product_name="Dell Infrastructure",
            contact_person="Dell Contact",
            email="dell@example.com",
            phone="2222222222",
            status="Active",
            notes="Infrastructure OEM",
        )

        oem_three = OEMPartner(
            account_id=account_a.account_id,
            partner_name="Microsoft",
            product_name="Microsoft Cloud",
            contact_person="Microsoft Contact",
            email="microsoft@example.com",
            phone="3333333333",
            status="Active",
            notes="Cloud OEM",
        )

        other_account_oem = OEMPartner(
            account_id=account_b.account_id,
            partner_name="Other Account OEM",
            product_name="Other Product",
            contact_person="Other Contact",
            email="other@example.com",
            phone="4444444444",
            status="Active",
        )

        db.session.add_all([
            oem_one,
            oem_two,
            oem_three,
            other_account_oem,
        ])

        db.session.commit()

        application.config["B3_OPPORTUNITY_A_ID"] = (
            opportunity_a.opportunity_id
        )
        application.config["B3_OPPORTUNITY_B_ID"] = (
            opportunity_b.opportunity_id
        )
        application.config["B3_OTHER_ACCOUNT_OPPORTUNITY_ID"] = (
            opportunity_other_account.opportunity_id
        )

        application.config["B3_OEM_ONE_ID"] = (
            oem_one.oem_partner_id
        )
        application.config["B3_OEM_TWO_ID"] = (
            oem_two.oem_partner_id
        )
        application.config["B3_OEM_THREE_ID"] = (
            oem_three.oem_partner_id
        )
        application.config["B3_OTHER_ACCOUNT_OEM_ID"] = (
            other_account_oem.oem_partner_id
        )

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

    data = response.get_json()

    token = data.get("access_token")

    assert token is not None

    return token


def auth(token):
    return {
        "Authorization": f"Bearer {token}",
    }


# ================================================================
# OEM REGISTRY
# ================================================================


def test_b3_create_oem(client):
    token = login(client, "sm@example.com")

    response = client.post(
        "/api/oem/",
        json={
            "account_id": 1,
            "partner_name": "VMware",
            "product_name": "VMware Cloud",
            "contact_person": "VMware Contact",
            "email": "vmware@example.com",
            "phone": "5555555555",
        },
        headers=auth(token),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "OEM Partner created"
    assert data["id"]


def test_b3_get_oem(client, app):
    token = login(client, "sm@example.com")

    oem_id = app.config["B3_OEM_ONE_ID"]

    response = client.get(
        f"/api/oem/{oem_id}",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["partner_name"] == "Cisco"
    assert data["product_name"] == "Cisco Networking"
    assert data["contact_person"] == "Cisco Contact"
    assert data["email"] == "cisco@example.com"


def test_b3_update_oem(client, app):
    token = login(client, "sm@example.com")

    oem_id = app.config["B3_OEM_ONE_ID"]

    response = client.put(
        f"/api/oem/{oem_id}",
        json={
            "product_name": "Cisco Enterprise Networking",
            "notes": "Updated B3 OEM",
        },
        headers=auth(token),
    )

    assert response.status_code == 200

    with app.app_context():
        oem = OEMPartner.query.get(oem_id)

        assert (
            oem.product_name
            == "Cisco Enterprise Networking"
        )
        assert oem.notes == "Updated B3 OEM"


def test_b3_delete_oem(client, app):
    token = login(client, "sm@example.com")

    oem_id = app.config["B3_OEM_THREE_ID"]

    response = client.delete(
        f"/api/oem/{oem_id}",
        headers=auth(token),
    )

    assert response.status_code == 200

    with app.app_context():
        assert OEMPartner.query.get(oem_id) is None


# ================================================================
# OEM CONTACT VISIBILITY
# ================================================================


def test_b3_employee_cannot_see_oem_contact_fields(client, app):
    token = login(client, "sales@example.com")

    oem_id = app.config["B3_OEM_ONE_ID"]

    response = client.get(
        f"/api/oem/{oem_id}",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "contact_person" not in data
    assert "email" not in data
    assert "phone" not in data


def test_b3_leadership_can_see_oem_contact_fields(client, app):
    token = login(client, "sm@example.com")

    oem_id = app.config["B3_OEM_ONE_ID"]

    response = client.get(
        f"/api/oem/{oem_id}",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["contact_person"] == "Cisco Contact"
    assert data["email"] == "cisco@example.com"
    assert data["phone"] == "1111111111"


# ================================================================
# OPPORTUNITY OEM ASSOCIATIONS
# ================================================================


def test_b3_attach_first_oem(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]
    oem_id = app.config["B3_OEM_ONE_ID"]

    response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == (
        "OEM Partner associated with opportunity"
    )
    assert data["opportunity_oem_id"]


def test_b3_multiple_oems_can_be_attached(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]

    first = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": app.config["B3_OEM_ONE_ID"],
        },
        headers=auth(token),
    )

    second = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": app.config["B3_OEM_TWO_ID"],
        },
        headers=auth(token),
    )

    third = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": app.config["B3_OEM_THREE_ID"],
        },
        headers=auth(token),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 201

    response = client.get(
        f"/api/opportunities/{opportunity_id}/oems",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 3

    ids = {
        row["oem_partner_id"]
        for row in data
    }

    assert ids == {
        app.config["B3_OEM_ONE_ID"],
        app.config["B3_OEM_TWO_ID"],
        app.config["B3_OEM_THREE_ID"],
    }


def test_b3_duplicate_oem_association_rejected(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]
    oem_id = app.config["B3_OEM_ONE_ID"]

    first = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    second = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_b3_invalid_opportunity_rejected(client, app):
    token = login(client, "sales@example.com")

    oem_id = app.config["B3_OEM_ONE_ID"]

    response = client.post(
        "/api/opportunities/999999/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert response.status_code == 404


def test_b3_invalid_oem_rejected(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]

    response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": 999999,
        },
        headers=auth(token),
    )

    assert response.status_code == 404


def test_b3_missing_oem_id_rejected(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]

    response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={},
        headers=auth(token),
    )

    assert response.status_code == 400


def test_b3_other_account_oem_cannot_be_attached(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]
    oem_id = app.config["B3_OTHER_ACCOUNT_OEM_ID"]

    response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert response.status_code in (403, 404)


def test_b3_unauthorized_opportunity_cannot_be_accessed(client, app):
    token = login(client, "se@example.com")

    opportunity_id = (
        app.config["B3_OTHER_ACCOUNT_OPPORTUNITY_ID"]
    )

    response = client.get(
        f"/api/opportunities/{opportunity_id}/oems",
        headers=auth(token),
    )

    assert response.status_code == 404


def test_b3_get_associations_returns_oem_details(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]

    for oem_key in (
        "B3_OEM_ONE_ID",
        "B3_OEM_TWO_ID",
    ):
        response = client.post(
            f"/api/opportunities/{opportunity_id}/oems",
            json={
                "oem_partner_id": app.config[oem_key],
            },
            headers=auth(token),
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/opportunities/{opportunity_id}/oems",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    names = {
        row["partner_name"]
        for row in data
    }

    assert names == {
        "Cisco",
        "Dell",
    }

    # Sales Executive must not receive OEM contact data.
    for row in data:
        assert "contact_person" not in row
        assert "email" not in row
        assert "phone" not in row


def test_b3_leadership_get_associations_includes_contacts(client, app):
    token = login(client, "sm@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]
    oem_id = app.config["B3_OEM_ONE_ID"]

    response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/opportunities/{opportunity_id}/oems",
        headers=auth(token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 1

    assert data[0]["contact_person"] == "Cisco Contact"
    assert data[0]["email"] == "cisco@example.com"
    assert data[0]["phone"] == "1111111111"


def test_b3_remove_association(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]
    oem_id = app.config["B3_OEM_ONE_ID"]

    create_response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert create_response.status_code == 201

    delete_response = client.delete(
        f"/api/opportunities/{opportunity_id}/oems/{oem_id}",
        headers=auth(token),
    )

    assert delete_response.status_code == 200

    response = client.get(
        f"/api/opportunities/{opportunity_id}/oems",
        headers=auth(token),
    )

    assert response.status_code == 200
    assert response.get_json() == []


def test_b3_removing_association_does_not_delete_oem(client, app):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]
    oem_id = app.config["B3_OEM_ONE_ID"]

    create_response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert create_response.status_code == 201

    delete_response = client.delete(
        f"/api/opportunities/{opportunity_id}/oems/{oem_id}",
        headers=auth(token),
    )

    assert delete_response.status_code == 200

    # The association is gone, but the OEM registry record remains.
    with app.app_context():
        oem = OEMPartner.query.get(oem_id)

        assert oem is not None
        assert oem.partner_name == "Cisco"


def test_b3_same_oem_can_be_used_by_multiple_opportunities(client, app):
    token = login(client, "sales@example.com")

    opportunity_a = app.config["B3_OPPORTUNITY_A_ID"]
    opportunity_b = app.config["B3_OPPORTUNITY_B_ID"]
    oem_id = app.config["B3_OEM_ONE_ID"]

    first = client.post(
        f"/api/opportunities/{opportunity_a}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    second = client.post(
        f"/api/opportunities/{opportunity_b}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    with app.app_context():
        associations = OpportunityOEM.query.filter_by(
            oem_partner_id=oem_id,
        ).all()

        assert len(associations) == 2


def test_b3_association_does_not_change_opportunity_stage(
    client,
    app,
):
    token = login(client, "sales@example.com")

    opportunity_id = app.config["B3_OPPORTUNITY_A_ID"]
    oem_id = app.config["B3_OEM_ONE_ID"]

    with app.app_context():
        opportunity = Opportunity.query.get(
            opportunity_id
        )
        original_stage_id = opportunity.stage_id

    response = client.post(
        f"/api/opportunities/{opportunity_id}/oems",
        json={
            "oem_partner_id": oem_id,
        },
        headers=auth(token),
    )

    assert response.status_code == 201

    with app.app_context():
        opportunity = Opportunity.query.get(
            opportunity_id
        )

        assert opportunity.stage_id == original_stage_id
