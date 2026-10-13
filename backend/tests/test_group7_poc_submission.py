import pytest
from datetime import date

from app import create_app
from app.database import db
from app.auth.password import hash_password
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.account.account import Account
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster
from app.models.phase2 import POCTeamMember
from app.services.opportunity_service import OpportunityService
from app.services.phase2_service import Phase2Service
from app.constants.roles import (
    LEADERSHIP, SALES_EXECUTIVE, SOLUTION_ENGINEER, DELIVERY_MANAGER,
    DEVOPS_ENGINEER, DATA_ANALYST,
)
from app.models.system.notification import Notification
from app.models.system.audit_log import AuditLog
from app.services.lifecycle_transition_service import TransitionConflict, TransitionInvalid
from app.auth.authorization import AuthorizationDenied


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path/'group7.db'}",
        "JWT_SECRET_KEY": "group7-test-secret",
    })
    with app.app_context():
        db.drop_all(); db.create_all()
        for order, name in enumerate(("Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"), 1):
            db.session.add(StageMaster(stage_name=name, display_order=order, requires_poc=name == "POC", is_closed=False, is_won=False))
        ids = {}
        for role in [LEADERSHIP, SALES_EXECUTIVE, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST]:
            u = User(
                full_name=role,
                email=role.lower().replace(" ", "_") + "@group7.local",
                password_hash=hash_password("Password123!"),
                status="APPROVED", active=True,
            )
            u.roles.append(UserRole(role=role)); db.session.add(u)
        db.session.flush()
        for u in User.query.all(): ids[u.roles[0].role] = u.user_id
        account = Account(account_name="Group7 Acme", is_active=True); db.session.add(account); db.session.flush()
        app.config.update(G7_USERS=ids, G7_ACCOUNT=account.account_id)
        db.session.commit()
    return app


def U(app, role):
    return db.session.get(User, app.config["G7_USERS"][role])


def make_poc(app, submitter_role=DEVOPS_ENGINEER, second=False):
    se = U(app, SOLUTION_ENGINEER)
    submitter = U(app, submitter_role)
    with app.app_context():
        oid = OpportunityService.create_opportunity(
            {"account_id": app.config["G7_ACCOUNT"], "opportunity_name": "Group7", "estimated_value": 100, "description": "d", "pain_points": "p"},
            U(app, SALES_EXECUTIVE), SALES_EXECUTIVE,
        ).opportunity_id
        o = db.session.get(Opportunity, oid)
        o.lifecycle_stage = "POC"; o.review_status = "Approved"; o.outcome = "Open"; o.operational_status = "Active"
        db.session.add(OpportunityTeam(opportunity_id=oid, user_id=se.user_id, role=SOLUTION_ENGINEER))
        db.session.commit()
        p = Phase2Service.request_poc(oid, {"target_date": date.today()}, se, SOLUTION_ENGINEER)
        Phase2Service.assign_poc_team(p.poc_id, [submitter.user_id], U(app, DELIVERY_MANAGER), DELIVERY_MANAGER)
        p = db.session.get(type(p), p.poc_id)
        if second:
            return oid, p, submitter, se
        return oid, p, submitter, se


def test_assigned_devops_submission_is_authoritative_and_notifies_se(app):
    with app.app_context():
        oid, p, submitter, se = make_poc(app, DEVOPS_ENGINEER)
        version = p.row_version
        result = Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/result", "row_version": version}, submitter, DEVOPS_ENGINEER)
        assert result.status == "Submitted"
        assert result.result_view_link == "https://example.com/result"
        assert result.submitted_by == submitter.user_id
        assert result.submitted_at is not None
        assert result.row_version == version + 1
        audit = AuditLog.query.filter_by(entity_type="POC", entity_id=p.poc_id, action="POC_SUBMITTED").one()
        assert audit.performed_by == submitter.user_id
        note = Notification.query.filter_by(recipient_user_id=se.user_id, notification_type="POC_SUBMITTED", entity_id=p.poc_id).one()
        assert note.recipient_user_id == se.user_id
        assert Notification.query.filter_by(notification_type="POC_SUBMITTED", entity_id=p.poc_id).count() == 1


def test_assigned_data_analyst_can_submit(app):
    with app.app_context():
        _, p, submitter, _ = make_poc(app, DATA_ANALYST)
        Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/data", "row_version": p.row_version}, submitter, DATA_ANALYST)
        assert db.session.get(type(p), p.poc_id).status == "Submitted"


def test_unassigned_devops_cannot_submit_other_poc(app):
    with app.app_context():
        _, p, _, _ = make_poc(app, DEVOPS_ENGINEER)
        other = U(app, DATA_ANALYST)
        with pytest.raises(AuthorizationDenied):
            Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/x", "row_version": p.row_version}, other, DATA_ANALYST)


def test_unauthorized_roles_cannot_submit(app):
    with app.app_context():
        _, p, _, _ = make_poc(app, DEVOPS_ENGINEER)
        se = U(app, SOLUTION_ENGINEER)
        with pytest.raises(AuthorizationDenied):
            Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/x", "row_version": p.row_version}, se, SOLUTION_ENGINEER)


def test_client_cannot_control_submission_fields(app):
    with app.app_context():
        _, p, submitter, _ = make_poc(app)
        with pytest.raises(TransitionInvalid):
            Phase2Service.submit_poc(
                p.poc_id,
                {"result_view_link": "https://example.com/x", "row_version": p.row_version, "submitted_by": 999, "submitted_at": "2020-01-01", "status": "Completed"},
                submitter, DEVOPS_ENGINEER,
            )


def test_invalid_link_is_rejected(app):
    with app.app_context():
        _, p, submitter, _ = make_poc(app)
        with pytest.raises(TransitionInvalid):
            Phase2Service.submit_poc(p.poc_id, {"result_view_link": "not-a-url", "row_version": p.row_version}, submitter, DEVOPS_ENGINEER)


def test_stale_version_does_not_mutate_poc(app):
    with app.app_context():
        _, p, submitter, _ = make_poc(app)
        original = p.row_version
        with pytest.raises(TransitionConflict):
            Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/x", "row_version": original - 1}, submitter, DEVOPS_ENGINEER)
        db.session.rollback()
        fresh = db.session.get(type(p), p.poc_id)
        assert fresh.row_version == original
        assert fresh.result_view_link is None
        assert fresh.submitted_at is None


def test_second_normal_submission_cannot_overwrite_result(app):
    with app.app_context():
        _, p, submitter, _ = make_poc(app)
        Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/first", "row_version": p.row_version}, submitter, DEVOPS_ENGINEER)
        fresh = db.session.get(type(p), p.poc_id)
        first_at = fresh.submitted_at
        with pytest.raises(TransitionInvalid):
            Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/second", "row_version": fresh.row_version}, submitter, DEVOPS_ENGINEER)
        db.session.rollback()
        fresh = db.session.get(type(p), p.poc_id)
        assert fresh.result_view_link == "https://example.com/first"
        assert fresh.submitted_by == submitter.user_id
        assert fresh.submitted_at == first_at


def test_closed_opportunity_rejects_submission(app):
    with app.app_context():
        _, p, submitter, _ = make_poc(app)
        o = db.session.get(Opportunity, p.opportunity_id)
        o.outcome = "Closed Won"; o.operational_status = "Closed"; db.session.commit()
        with pytest.raises(AuthorizationDenied):
            Phase2Service.submit_poc(p.poc_id, {"result_view_link": "https://example.com/x", "row_version": p.row_version}, submitter, DEVOPS_ENGINEER)
