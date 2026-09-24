import pytest

from app import create_app
from app.auth.authorization import AuthorizationDenied
from app.auth.password import hash_password
from app.constants.roles import (
    ADMIN,
    DATA_ANALYST,
    DEVOPS_ENGINEER,
    DELIVERY_MANAGER,
    LEADERSHIP,
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
from app.models.opportunity.stage_master import StageMaster
from app.models.phase2 import RFXContext
from app.models.system.audit_log import AuditLog
from app.services.lifecycle_transition_service import (
    LifecycleTransitionService,
    TransitionConflict,
    TransitionInvalid,
)
from app.services.phase2_service import Phase2Service
from app.services.opportunity_service import OpportunityService


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'group3.db'}",
            "JWT_SECRET_KEY": "group3-test-secret",
        }
    )

    with application.app_context():
        db.drop_all()
        db.create_all()

        account = Account(
            account_name="Group 3 Canonical Account",
            is_active=True,
        )
        db.session.add(account)

        for role in [
            LEADERSHIP,
            ADMIN,
            SALES_MANAGER,
            SALES_EXECUTIVE,
            PRE_SALES_MANAGER,
            SOLUTION_ENGINEER,
            DELIVERY_MANAGER,
            DEVOPS_ENGINEER,
            DATA_ANALYST,
        ]:
            user = User(
                full_name=f"Group3 {role}",
                email=f"{role.lower().replace(' ', '_').replace('-', '_')}@group3.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            user.roles.append(UserRole(role=role))
            db.session.add(user)

        db.session.flush()

        for order, name in enumerate(
            ("Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"),
            1,
        ):
            db.session.add(
                StageMaster(
                    stage_name=name,
                    display_order=order,
                    requires_poc=(name == "POC"),
                    is_closed=False,
                    is_won=False,
                )
            )

        db.session.commit()

        application.config["P1_ACCOUNT"] = account.account_id
        application.config["P1_USERS"] = {
            u.role_names()[0]: u.user_id for u in User.query.all()
        }

    return application


def _rfx_opp(app, name="Group3 RFX"):
    from tests.test_opportunity_lifecycle import make_lead, submit, approve, user

    oid = make_lead(app, SALES_EXECUTIVE, name)
    submit(app, oid)
    approve(app, oid)

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        db.session.add(
            OpportunityTeam(
                opportunity_id=oid,
                user_id=se.user_id,
                role=SOLUTION_ENGINEER,
            )
        )
        db.session.commit()

        opp = Opportunity.query.get(oid)

        LifecycleTransitionService.transition(
            oid,
            "RFX",
            opp.row_version,
            se,
            SOLUTION_ENGINEER,
        )

        return oid


def test_assigned_se_can_create_and_update_rfx_with_optimistic_concurrency(app):
    oid = _rfx_opp(app)

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        ctx = Phase2Service.update_rfx(
            oid,
            {"drive_folder_link": "https://drive.google.com/rfx-folder"},
            se,
            SOLUTION_ENGINEER,
        )

        assert ctx.drive_link == "https://drive.google.com/rfx-folder"
        assert ctx.row_version == 1
        assert ctx.created_by == se.user_id
        assert ctx.updated_by == se.user_id

        ctx = Phase2Service.update_rfx(
            oid,
            {
                "drive_link": "https://drive.google.com/rfx-folder-v2",
                "row_version": 1,
            },
            se,
            SOLUTION_ENGINEER,
        )

        assert ctx.drive_link.endswith("v2")
        assert ctx.row_version == 2

        with pytest.raises(TransitionConflict):
            Phase2Service.update_rfx(
                oid,
                {
                    "drive_link": "https://drive.google.com/stale",
                    "row_version": 1,
                },
                se,
                SOLUTION_ENGINEER,
            )

        db.session.rollback()

        assert RFXContext.query.filter_by(opportunity_id=oid).count() == 1
        assert (
            RFXContext.query.filter_by(opportunity_id=oid)
            .first()
            .drive_link.endswith("v2")
        )


def test_rfx_update_rejects_non_rfx_fields(app):
    oid = _rfx_opp(app, "RFX Field Security")

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        with pytest.raises(TransitionInvalid):
            Phase2Service.update_rfx(
                oid,
                {
                    "drive_link": "https://drive.google.com/rfx-folder",
                    "row_version": 0,
                    "lifecycle_stage": "Negotiations",
                    "outcome": "Closed Won",
                    "created_by": 999,
                },
                se,
                SOLUTION_ENGINEER,
            )

        db.session.rollback()

        assert RFXContext.query.filter_by(opportunity_id=oid).count() == 0
        assert Opportunity.query.get(oid).lifecycle_stage == "RFX"
        assert Opportunity.query.get(oid).outcome == "Open"


def test_rfx_authorization_requires_assigned_se(app):
    oid = _rfx_opp(app, "RFX Authorization")

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        assigned = user(app, SOLUTION_ENGINEER)

        unrelated = User(
            full_name="Unrelated Group3 SE",
            email="unrelated-group3-se@phase1.test",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        unrelated.roles.append(UserRole(role=SOLUTION_ENGINEER))
        db.session.add(unrelated)
        db.session.commit()

        with pytest.raises(AuthorizationDenied):
            Phase2Service.update_rfx(
                oid,
                {"drive_link": "https://drive.google.com/blocked"},
                unrelated,
                SOLUTION_ENGINEER,
            )

        db.session.rollback()

        sales_exec = user(app, SALES_EXECUTIVE)

        with pytest.raises(AuthorizationDenied):
            Phase2Service.update_rfx(
                oid,
                {"drive_link": "https://drive.google.com/blocked"},
                sales_exec,
                SALES_EXECUTIVE,
            )

        db.session.rollback()

        psm = user(app, PRE_SALES_MANAGER)

        with pytest.raises(AuthorizationDenied):
            Phase2Service.update_rfx(
                oid,
                {"drive_link": "https://drive.google.com/blocked"},
                psm,
                PRE_SALES_MANAGER,
            )

        db.session.rollback()

        assert RFXContext.query.filter_by(opportunity_id=oid).count() == 0
        assert assigned.user_id != unrelated.user_id


def test_rfx_update_rejects_invalid_drive_reference(app):
    oid = _rfx_opp(app, "RFX Validation")

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        for bad in (
            None,
            "",
            "not-a-url",
            "https://example.com/rfx",
        ):
            with pytest.raises(TransitionInvalid):
                Phase2Service.update_rfx(
                    oid,
                    {"drive_link": bad},
                    se,
                    SOLUTION_ENGINEER,
                )

            db.session.rollback()

        assert RFXContext.query.filter_by(opportunity_id=oid).count() == 0


def test_rfx_update_audits_old_and_new_reference(app):
    oid = _rfx_opp(app, "RFX Audit")

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        Phase2Service.update_rfx(
            oid,
            {"drive_link": "https://drive.google.com/one"},
            se,
            SOLUTION_ENGINEER,
        )

        Phase2Service.update_rfx(
            oid,
            {
                "drive_link": "https://drive.google.com/two",
                "row_version": 1,
            },
            se,
            SOLUTION_ENGINEER,
        )

        rows = AuditLog.query.filter_by(
            entity_type="Opportunity",
            entity_id=oid,
        ).all()

        descriptions = [r.description or "" for r in rows]

        assert any(
            "https://drive.google.com/one" in d
            and "https://drive.google.com/two" in d
            for d in descriptions
        )

        assert any(r.action == "RFX_CONTEXT_CREATED" for r in rows)
        assert any(r.action == "RFX_CONTEXT_UPDATED" for r in rows)


def test_rfx_to_poc_uses_persisted_drive_context_and_opportunity_version(app):
    oid = _rfx_opp(app, "RFX POC Authoritative Context")

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        opp = Opportunity.query.get(oid)

        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.transition(
                oid,
                "POC",
                opp.row_version,
                se,
                SOLUTION_ENGINEER,
            )

        Phase2Service.update_rfx(
            oid,
            {"drive_link": "https://drive.google.com/rfx-folder"},
            se,
            SOLUTION_ENGINEER,
        )

        opp = Opportunity.query.get(oid)

        LifecycleTransitionService.transition(
            oid,
            "POC",
            opp.row_version,
            se,
            SOLUTION_ENGINEER,
        )

        assert Opportunity.query.get(oid).lifecycle_stage == "POC"


def test_rfx_security_rejects_role_and_assignment_spoofing_and_generic_patch_fields(
    app,
):
    oid = _rfx_opp(app, "RFX Spoofing")

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        with pytest.raises(AuthorizationDenied):
            Phase2Service.update_rfx(
                oid,
                {
                    "drive_link": "https://drive.google.com/rfx-folder",
                    "role": SOLUTION_ENGINEER,
                    "solution_engineer_id": se.user_id,
                    "lifecycle_stage": "RFX",
                },
                user(app, SALES_EXECUTIVE),
                SALES_EXECUTIVE,
            )

        db.session.rollback()

        # An assigned Solution Engineer must still be unable to spoof
        # role/assignment/lifecycle fields through the RFX mutation path.
        with pytest.raises(TransitionInvalid):
            Phase2Service.update_rfx(
                oid,
                {
                    "drive_link": "https://drive.google.com/rfx-folder",
                    "role": SALES_EXECUTIVE,
                    "solution_engineer_id": user(app, SALES_EXECUTIVE).user_id,
                    "lifecycle_stage": "Negotiations",
                },
                se,
                SOLUTION_ENGINEER,
            )

        db.session.rollback()

        from app.schemas.opportunity_schema import OpportunityUpdateSchema

        with pytest.raises(Exception):
            OpportunityUpdateSchema().load(
                {"drive_link": "https://drive.google.com/rfx-folder"}
            )


def test_closed_opportunity_cannot_mutate_rfx(app):
    oid = _rfx_opp(app, "RFX Closed")

    from tests.test_opportunity_lifecycle import user

    with app.app_context():
        se = user(app, SOLUTION_ENGINEER)

        opp = Opportunity.query.get(oid)

        LifecycleTransitionService.close_won(
            oid,
            opp.row_version,
            user(app, PRE_SALES_MANAGER),
            PRE_SALES_MANAGER,
        )

        closed = Opportunity.query.get(oid)

        with pytest.raises(AuthorizationDenied):
            Phase2Service.update_rfx(
                oid,
                {"drive_link": "https://drive.google.com/closed"},
                se,
                SOLUTION_ENGINEER,
            )

        db.session.rollback()

        assert closed.operational_status == "Closed"