
import pytest

from app import create_app
from app.database import db
from app.auth.password import hash_password
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.account.account import Account
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.closed_won_request import ClosedWonRequest
from app.models.system.notification import Notification
from app.models.system.tag import Tag
from app.models.opportunity.stage_master import StageMaster
from app.constants.roles import (
    LEADERSHIP, SALES_MANAGER, SALES_EXECUTIVE, PRE_SALES_MANAGER,
    SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST,
)
from app.services.lifecycle_transition_service import (
    LifecycleTransitionService, TransitionConflict, TransitionInvalid,
)
from app.services.activity_service import ActivityService


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path/'group8.db'}",
        "JWT_SECRET_KEY": "group8-secret",
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        for name in ["Economic Buyer", "Technical Champion"]:
            db.session.add(Tag(name=name, is_active=True))
        for order, name in enumerate(("Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"), 1):
            db.session.add(StageMaster(
                stage_name=name, display_order=order,
                requires_poc=name == "POC", is_closed=False, is_won=False,
            ))
        roles = [
            LEADERSHIP, SALES_MANAGER, SALES_EXECUTIVE, PRE_SALES_MANAGER,
            SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST,
        ]
        ids = {}
        for role in roles:
            u = User(
                full_name=role,
                email=role.lower().replace(" ", "_") + "@group8.test",
                password_hash=hash_password("Password123!"),
                status="APPROVED",
                active=True,
            )
            u.roles.append(UserRole(role=role))
            db.session.add(u)
        db.session.flush()
        for u in User.query.all():
            ids[u.roles[0].role] = u.user_id
        account = Account(account_name="Group 8 Account", is_active=True)
        db.session.add(account)
        db.session.flush()
        app.config.update(G8_USERS=ids, G8_ACCOUNT=account.account_id)
        db.session.commit()
    return app


def U(app, role):
    return User.query.get(app.config["G8_USERS"][role])


def make_opportunity(app, stage="Qualified"):
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        stage_row = StageMaster.query.filter_by(stage_name=stage).one()
        o = Opportunity(
            account_id=app.config["G8_ACCOUNT"],
            created_by=U(app, SALES_EXECUTIVE).user_id,
            stage_id=stage_row.stage_id,
            opportunity_name=f"Group 8 {stage}",
            description="description",
            pain_points="pain",
            estimated_value=100000,
            lifecycle_stage=stage,
            outcome="Open",
            operational_status="Active",
            review_status="Approved",
            row_version=1,
            status="Active",
            is_active=True,
        )
        db.session.add(o)
        db.session.flush()
        db.session.add(OpportunityTeam(
            opportunity_id=o.opportunity_id,
            user_id=se.user_id,
            role=SOLUTION_ENGINEER,
        ))
        db.session.commit()
        return o.opportunity_id


def test_assigned_se_can_request_closed_closure_without_closing(app):
    oid = make_opportunity(app, "Qualified")
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        o = Opportunity.query.get(oid)
        result = LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
        )
        assert result.outcome == "Open"
        assert result.operational_status == "Active"
        assert result.lifecycle_stage == "Qualified"
        assert result.row_version == 2
        req = ClosedWonRequest.query.filter_by(opportunity_id=oid).one()
        assert req.requested_outcome == "Closed Won"
        assert req.status == "Pending"
        assert req.requested_by == se.user_id


@pytest.mark.parametrize("outcome,reason,explanation", [
    ("Closed Lost", "Competitor", None),
    ("Closed Lost", "Other", "Client selected another provider"),
])
def test_assigned_se_can_request_closed_lost(app, outcome, reason, explanation):
    oid = make_opportunity(app, "RFX")
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, outcome, reason, explanation, se, SOLUTION_ENGINEER
        )
        req = ClosedWonRequest.query.filter_by(opportunity_id=oid).one()
        assert (req.requested_outcome, req.requested_reason, req.requested_explanation) == (
            outcome, reason, explanation
        )
        assert Opportunity.query.get(oid).outcome == "Open"


@pytest.mark.parametrize("stage", ["POC", "Negotiations", "Lead"])
def test_no_poc_closure_request_is_limited_to_qualified_or_rfx(app, stage):
    oid = make_opportunity(app, stage)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        o = Opportunity.query.get(oid)
        with pytest.raises(Exception):
            LifecycleTransitionService.request_closure(
                oid, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
            )
        assert ClosedWonRequest.query.filter_by(opportunity_id=oid).count() == 0
        assert Opportunity.query.get(oid).outcome == "Open"


def test_unassigned_se_cannot_request_closure(app):
    oid = make_opportunity(app)
    with app.app_context():
        assigned = U(app, SOLUTION_ENGINEER)
        other = User(
            full_name="Other SE",
            email="other-se@group8.test",
            password_hash=hash_password("Password123!"),
            status="APPROVED",
            active=True,
        )
        other.roles.append(UserRole(role=SOLUTION_ENGINEER))
        db.session.add(other)
        db.session.commit()
        o = Opportunity.query.get(oid)
        from app.auth.authorization import AuthorizationDenied
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.request_closure(
                oid, o.row_version, "Closed Won", None, None, other, SOLUTION_ENGINEER
            )
        assert ClosedWonRequest.query.count() == 0


def test_cross_opportunity_idor_is_blocked(app):
    oid_a = make_opportunity(app)
    oid_b = make_opportunity(app)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        # Remove SE membership from B, leaving the authenticated SE assigned only to A.
        OpportunityTeam.query.filter_by(
            opportunity_id=oid_b, user_id=se.user_id, role=SOLUTION_ENGINEER
        ).delete()
        db.session.commit()
        o = Opportunity.query.get(oid_b)
        from app.auth.authorization import AuthorizationDenied
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.request_closure(
                oid_b, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
            )


def test_closed_lost_validation(app):
    oid = make_opportunity(app)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        o = Opportunity.query.get(oid)
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.request_closure(
                oid, o.row_version, "Closed Lost", None, None, se, SOLUTION_ENGINEER
            )
        with pytest.raises(TransitionInvalid):
            LifecycleTransitionService.request_closure(
                oid, o.row_version, "Closed Lost", "Other", None, se, SOLUTION_ENGINEER
            )


def test_psm_reject_keeps_opportunity_open_and_preserves_request(app):
    oid = make_opportunity(app)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        psm = U(app, PRE_SALES_MANAGER)
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
        )
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.resolve_closure_request(
            oid, o.row_version, False, "Needs more commercial review", psm, PRE_SALES_MANAGER
        )
        o = Opportunity.query.get(oid)
        req = ClosedWonRequest.query.filter_by(opportunity_id=oid).one()
        assert req.status == "Rejected"
        assert o.outcome == "Open"
        assert o.operational_status == "Active"
        assert o.lifecycle_stage == "Qualified"


def test_psm_approves_closed_won_and_closes_atomically(app):
    oid = make_opportunity(app, "RFX")
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        psm = U(app, PRE_SALES_MANAGER)
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
        )
        o = Opportunity.query.get(oid)
        result = LifecycleTransitionService.resolve_closure_request(
            oid, o.row_version, True, None, psm, PRE_SALES_MANAGER
        )
        assert result.outcome == "Closed Won"
        assert result.operational_status == "Closed"
        assert result.lifecycle_stage == "RFX"
        req = ClosedWonRequest.query.filter_by(opportunity_id=oid).one()
        assert req.status == "Approved"
        assert result.final_revenue == 100000


def test_psm_approves_closed_lost_using_request_reason(app):
    oid = make_opportunity(app)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        psm = U(app, PRE_SALES_MANAGER)
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Lost", "Other",
            "Client selected another provider.", se, SOLUTION_ENGINEER
        )
        o = Opportunity.query.get(oid)
        result = LifecycleTransitionService.resolve_closure_request(
            oid, o.row_version, True, None, psm, PRE_SALES_MANAGER
        )
        assert result.outcome == "Closed Lost"
        assert result.operational_status == "Closed"
        assert result.lost_reason == "Other"
        assert result.lost_explanation == "Client selected another provider."
        assert ClosedWonRequest.query.filter_by(opportunity_id=oid, status="Approved").count() == 1


def test_non_psm_cannot_approve_and_se_cannot_self_approve(app):
    oid = make_opportunity(app)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        sales = U(app, SALES_EXECUTIVE)
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
        )
        o = Opportunity.query.get(oid)
        from app.auth.authorization import AuthorizationDenied
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.resolve_closure_request(
                oid, o.row_version, True, None, se, SOLUTION_ENGINEER
            )
        o = Opportunity.query.get(oid)
        with pytest.raises(AuthorizationDenied):
            LifecycleTransitionService.resolve_closure_request(
                oid, o.row_version, True, None, sales, SALES_EXECUTIVE
            )


def test_stale_request_and_duplicate_processing_are_rejected(app):
    oid = make_opportunity(app)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        psm = U(app, PRE_SALES_MANAGER)
        o = Opportunity.query.get(oid)
        stale = o.row_version
        LifecycleTransitionService.request_closure(
            oid, stale, "Closed Won", None, None, se, SOLUTION_ENGINEER
        )
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.resolve_closure_request(
                oid, stale, True, None, psm, PRE_SALES_MANAGER
            )
        fresh = Opportunity.query.get(oid)
        LifecycleTransitionService.resolve_closure_request(
            oid, fresh.row_version, True, None, psm, PRE_SALES_MANAGER
        )
        closed = Opportunity.query.get(oid)
        with pytest.raises(TransitionConflict):
            LifecycleTransitionService.resolve_closure_request(
                oid, closed.row_version, True, None, psm, PRE_SALES_MANAGER
            )


def test_repeated_requests_preserve_previous_history(app):
    oid = make_opportunity(app)
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        psm = U(app, PRE_SALES_MANAGER)
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
        )
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.resolve_closure_request(
            oid, o.row_version, False, "Rejected once", psm, PRE_SALES_MANAGER
        )
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Lost", "Competitor", None, se, SOLUTION_ENGINEER
        )
        rows = ClosedWonRequest.query.filter_by(opportunity_id=oid).order_by(ClosedWonRequest.request_id).all()
        assert len(rows) == 2
        assert [r.status for r in rows] == ["Rejected", "Pending"]
        assert rows[0].resolution_reason == "Rejected once"


def test_closed_won_creates_delivery_project_and_notifies_delivery_manager(app):
    oid = make_opportunity(app, "Qualified")
    with app.app_context():
        se = U(app, SOLUTION_ENGINEER)
        psm = U(app, PRE_SALES_MANAGER)
        dm = U(app, DELIVERY_MANAGER)
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.request_closure(
            oid, o.row_version, "Closed Won", None, None, se, SOLUTION_ENGINEER
        )
        o = Opportunity.query.get(oid)
        LifecycleTransitionService.resolve_closure_request(
            oid, o.row_version, True, None, psm, PRE_SALES_MANAGER
        )
        notifications = Notification.query.filter_by(
            recipient_user_id=dm.user_id,
            notification_type="DELIVERY_PROJECT_CREATED",
            entity_id=oid,
        ).count()
        assert notifications == 1
