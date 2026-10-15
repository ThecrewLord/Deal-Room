from datetime import date, datetime
import pytest
from app import create_app
from app.database import db
from app.auth.password import hash_password
from app.auth.authorization import AuthorizationDenied
from app.constants.roles import (
    LEADERSHIP, SALES_EXECUTIVE, SOLUTION_ENGINEER, DELIVERY_MANAGER,
    DEVOPS_ENGINEER, DATA_ANALYST,
)
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.account.account import Account
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.stage_master import StageMaster
from app.models.phase2 import (
    POCTeamMember, OpportunityPOCTeamMember, DeliveryProject,
    DeliveryProjectMember,
)
from app.services.phase2_service import Phase2Service
from app.services.delivery_performance_service import DeliveryPerformanceService


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path/'p2_delivery.db'}", "JWT_SECRET_KEY": "p2-delivery"})
    with application.app_context():
        db.drop_all(); db.create_all()
        for order, name in enumerate(("Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"), 1):
            db.session.add(StageMaster(stage_name=name, display_order=order, requires_poc=name == "POC", is_closed=False, is_won=False))
        users = {}
        for role in (LEADERSHIP, SALES_EXECUTIVE, SOLUTION_ENGINEER, DELIVERY_MANAGER, DEVOPS_ENGINEER, DATA_ANALYST):
            user = User(full_name=f"P2 {role}", email=f"{role.lower().replace(' ', '_')}@p2.test", password_hash=hash_password("Password123!"), active=True, status="APPROVED")
            user.roles.append(UserRole(role=role)); db.session.add(user); users[role] = user
        account = Account(account_name="P2 Delivery Account", is_active=True); db.session.add(account); db.session.flush()
        for role, user in users.items(): users[role] = db.session.get(User, user.user_id)
        application.config["P2_DELIVERY_USERS"] = {role: user.user_id for role, user in users.items()}
        application.config["P2_DELIVERY_ACCOUNT"] = account.account_id
        db.session.commit()
    return application


def user(app, role):
    return db.session.get(User, app.config["P2_DELIVERY_USERS"][role])


def make_opportunity(app, stage="POC", outcome="Open"):
    stage_row = StageMaster.query.filter_by(stage_name=stage).one()
    opportunity = Opportunity(
        account_id=app.config["P2_DELIVERY_ACCOUNT"], created_by=user(app, SALES_EXECUTIVE).user_id,
        sales_owner_id=user(app, SALES_EXECUTIVE).user_id, stage_id=stage_row.stage_id,
        opportunity_name=f"P2 {stage} Opportunity", estimated_value=120000, probability=40,
        expected_close_date=date.today(), lifecycle_stage=stage, outcome=outcome,
        operational_status="Closed" if outcome != "Open" else "Active", review_status="Approved",
        row_version=1, status="Closed" if outcome != "Open" else "Active", is_active=outcome == "Open",
    )
    db.session.add(opportunity); db.session.flush(); return opportunity


def test_poc_team_is_canonical_and_reused_for_repeat_cycle(app):
    with app.app_context():
        opportunity = make_opportunity(app)
        se = user(app, SOLUTION_ENGINEER); dm = user(app, DELIVERY_MANAGER); devops = user(app, DEVOPS_ENGINEER)
        db.session.add(OpportunityTeam(opportunity_id=opportunity.opportunity_id, user_id=se.user_id, role=SOLUTION_ENGINEER))
        poc = POCTracker(opportunity_id=opportunity.opportunity_id, poc_name="First POC", target_date=date.today(), requested_by=se.user_id, status="Draft", row_version=1)
        db.session.add(poc); db.session.commit()
        Phase2Service.assign_poc_team(poc.poc_id, [devops.user_id], dm, DELIVERY_MANAGER, expected_version=1)
        canonical = OpportunityPOCTeamMember.query.filter_by(opportunity_id=opportunity.opportunity_id).all()
        assert [(m.user_id, m.role) for m in canonical] == [(devops.user_id, DEVOPS_ENGINEER)]
        poc.status = "Completed"; poc.outcome = "Failure"; poc.outcome_notes = "Required written reason"; poc.row_version = 2; db.session.commit()
        new_poc = Phase2Service.request_new_poc(opportunity.opportunity_id, {"reason": "Customer requested another cycle", "row_version": 2}, se, SOLUTION_ENGINEER)
        assert OpportunityPOCTeamMember.query.filter_by(opportunity_id=opportunity.opportunity_id).count() == 1
        assert [(m.user_id, m.role) for m in new_poc.team_members] == [(devops.user_id, DEVOPS_ENGINEER)]
        assert POCTeamMember.query.filter_by(poc_id=poc.poc_id).count() == 1


def test_delivery_project_suggests_canonical_poc_team_but_keeps_separate_membership(app):
    with app.app_context():
        opportunity = make_opportunity(app, stage="Delivery", outcome="Closed Won")
        dm = user(app, DELIVERY_MANAGER); devops = user(app, DEVOPS_ENGINEER)
        db.session.add(OpportunityPOCTeamMember(opportunity_id=opportunity.opportunity_id, user_id=devops.user_id, role=DEVOPS_ENGINEER, assigned_by=dm.user_id))
        db.session.commit()
        project = Phase2Service.create_delivery_project(opportunity, user(app, SALES_EXECUTIVE), SALES_EXECUTIVE)
        db.session.flush()
        assert len(project.members) == 1
        assert project.members[0].user_id == devops.user_id
        assert project.members[0].is_suggested is True
        assert DeliveryProjectMember.query.filter_by(delivery_project_id=project.delivery_project_id).count() == 1


def test_delivery_performance_scope_and_due_date_limitation(app):
    with app.app_context():
        opportunity = make_opportunity(app, stage="Delivery", outcome="Closed Won")
        dm = user(app, DELIVERY_MANAGER); devops = user(app, DEVOPS_ENGINEER)
        project = DeliveryProject(opportunity_id=opportunity.opportunity_id, account_id=opportunity.account_id, manager_id=dm.user_id, status="Active", row_version=1)
        db.session.add(project); db.session.flush()
        db.session.add(DeliveryProjectMember(delivery_project_id=project.delivery_project_id, user_id=devops.user_id, is_done=False, assigned_by=dm.user_id, is_suggested=False))
        db.session.commit()
        result = DeliveryPerformanceService.get_team_performance(dm, DELIVERY_MANAGER)
        assert result["summary"]["delivery_team"] == 1
        assert result["summary"]["assigned_opportunities"] == 1
        assert result["summary"]["active_delivery_work"] == 1
        assert result["summary"]["overdue_work"] is None
        individual = DeliveryPerformanceService.get_employee_performance(dm, DELIVERY_MANAGER, devops.user_id)
        assert individual["metrics"]["active_delivery_work"] == 1
        assert [item["stage"] for item in individual["pipeline_by_stage"] if item["count"]] == ["Delivery"]


def test_delivery_performance_denies_non_manager(app):
    with app.app_context():
        with pytest.raises(AuthorizationDenied):
            DeliveryPerformanceService.get_team_performance(user(app, SALES_EXECUTIVE), SALES_EXECUTIVE)


def test_poc_assignment_queue_is_role_protected_and_reports_unassigned_work(app):
    with app.app_context():
        opportunity = make_opportunity(app)
        se = user(app, SOLUTION_ENGINEER)
        db.session.add(OpportunityTeam(opportunity_id=opportunity.opportunity_id, user_id=se.user_id, role=SOLUTION_ENGINEER))
        db.session.add(POCTracker(opportunity_id=opportunity.opportunity_id, poc_name="Queue POC", target_date=date.today(), requested_by=se.user_id, status="Draft"))
        db.session.commit()
        rows = Phase2Service.get_poc_assignment_queue(user(app, DELIVERY_MANAGER), DELIVERY_MANAGER, assignment_status="unassigned")
        assert len(rows) == 1
        assert rows[0]["opportunity_id"] == opportunity.opportunity_id
        assert rows[0]["team_assigned"] is False
        with pytest.raises(AuthorizationDenied):
            Phase2Service.get_poc_assignment_queue(user(app, SALES_EXECUTIVE), SALES_EXECUTIVE)


def test_stale_poc_team_reassignment_is_rejected(app):
    from app.services.lifecycle_transition_service import TransitionConflict
    with app.app_context():
        opportunity = make_opportunity(app)
        dm = user(app, DELIVERY_MANAGER); devops = user(app, DEVOPS_ENGINEER); analyst = user(app, DATA_ANALYST)
        poc = POCTracker(opportunity_id=opportunity.opportunity_id, poc_name="Reassign POC", target_date=date.today(), requested_by=user(app, SOLUTION_ENGINEER).user_id, status="Draft", row_version=1)
        db.session.add(poc); db.session.commit()
        Phase2Service.assign_poc_team(poc.poc_id, [devops.user_id], dm, DELIVERY_MANAGER, expected_version=1)
        with pytest.raises(TransitionConflict):
            Phase2Service.reassign_opportunity_poc_team(opportunity.opportunity_id, {"member_ids": [analyst.user_id], "expected_version": 1}, dm, DELIVERY_MANAGER)
        assert [m.user_id for m in OpportunityPOCTeamMember.query.filter_by(opportunity_id=opportunity.opportunity_id).all()] == [devops.user_id]


def test_delivery_team_update_rejects_stale_version_and_empty_team(app):
    from app.services.lifecycle_transition_service import TransitionConflict
    with app.app_context():
        opportunity = make_opportunity(app, stage="Delivery", outcome="Closed Won")
        dm = user(app, DELIVERY_MANAGER); devops = user(app, DEVOPS_ENGINEER)
        project = DeliveryProject(opportunity_id=opportunity.opportunity_id, account_id=opportunity.account_id, manager_id=dm.user_id, status="Active", row_version=2)
        db.session.add(project); db.session.flush()
        member = DeliveryProjectMember(delivery_project_id=project.delivery_project_id, user_id=devops.user_id, assigned_by=dm.user_id, is_suggested=True)
        db.session.add(member); db.session.commit()
        with pytest.raises(TransitionConflict):
            Phase2Service.assign_delivery_members(project.delivery_project_id, [], dm, DELIVERY_MANAGER, expected_version=1)
        assert DeliveryProjectMember.query.filter_by(delivery_project_id=project.delivery_project_id).count() == 1
        with pytest.raises(ValueError, match="At least one delivery team member"):
            Phase2Service.assign_delivery_members(project.delivery_project_id, [], dm, DELIVERY_MANAGER, expected_version=2)
        assert DeliveryProjectMember.query.filter_by(delivery_project_id=project.delivery_project_id).count() == 1


def test_concurrent_initial_poc_assignments_use_separate_sessions(app):
    """Exercise two concurrent initial assignments through independent thread-local sessions."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    with app.app_context():
        opportunity = make_opportunity(app)
        dm_id = user(app, DELIVERY_MANAGER).user_id
        devops_id = user(app, DEVOPS_ENGINEER).user_id
        analyst_id = user(app, DATA_ANALYST).user_id
        se = user(app, SOLUTION_ENGINEER)
        db.session.add(OpportunityTeam(opportunity_id=opportunity.opportunity_id, user_id=se.user_id, role=SOLUTION_ENGINEER))
        poc = POCTracker(opportunity_id=opportunity.opportunity_id, poc_name="Concurrent POC", target_date=date.today(), requested_by=se.user_id, status="Draft", row_version=1)
        db.session.add(poc); db.session.commit()
        oid, poc_id = opportunity.opportunity_id, poc.poc_id

    barrier = Barrier(2)
    def assign(member_id):
        with app.app_context():
            manager = db.session.get(User, dm_id)
            barrier.wait(timeout=5)
            try:
                Phase2Service.assign_poc_team(poc_id, [member_id], manager, DELIVERY_MANAGER, expected_version=1)
                return "success"
            except Exception:
                db.session.rollback()
                return "rejected"
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(assign, [devops_id, analyst_id]))

    with app.app_context():
        canonical = OpportunityPOCTeamMember.query.filter_by(opportunity_id=oid).all()
        assert outcomes.count("success") == 1
        assert len(canonical) == 1
        assert canonical[0].user_id in {devops_id, analyst_id}
