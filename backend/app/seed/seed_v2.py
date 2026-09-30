from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from werkzeug.security import generate_password_hash

from app.database import db
from app.constants.roles import (
    LEADERSHIP,
    ADMIN,
    SALES_MANAGER,
    SALES_EXECUTIVE,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
)

from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.account.account import Account
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.stage_history import StageHistory
from app.models.opportunity.opportunity_value_history import OpportunityValueHistory
from app.models.opportunity.stakeholder import Stakeholder
from app.models.system.tag import Tag
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.poc_history import POCHistory

from app.models.phase2 import (
    RFXContext,
    NegotiationContext,
    POCTeamMember,
    DeliveryProject,
    DeliveryProjectMember,
    Activity,
    FollowUp,
)


PREFIX = "PH18-"
SEED_PASSWORD = "ChangeMe123!"

ROLE_USERS = [
    (ADMIN, "Phase18 Admin", "ph18.admin@dataeko.ai"),
    (SALES_MANAGER, "Phase18 Sales Manager", "ph18.sales.manager@dataeko.ai"),
    (SALES_EXECUTIVE, "Phase18 Sales Executive", "ph18.sales.executive@dataeko.ai"),
    (PRE_SALES_MANAGER, "Phase18 Pre-Sales Manager", "ph18.pre.sales@dataeko.ai"),
    (SOLUTION_ENGINEER, "Phase18 Solution Engineer", "ph18.solution.engineer@dataeko.ai"),
    (DELIVERY_MANAGER, "Phase18 Delivery Manager", "ph18.delivery.manager@dataeko.ai"),
    (DEVOPS_ENGINEER, "Phase18 DevOps Engineer", "ph18.devops@dataeko.ai"),
    (DATA_ANALYST, "Phase18 Data Analyst", "ph18.data.analyst@dataeko.ai"),
]


STAGES = [
    ("Lead", 1, False),
    ("Qualified", 2, False),
    ("RFX", 3, False),
    ("POC", 4, True),
    ("Negotiations", 5, False),
    ("Delivery", 6, False),
]


def _ensure_stage_master():
    """Ensure canonical stages exist without deleting legacy/manual stage rows."""
    result = {}

    for stage_name, display_order, requires_poc in STAGES:
        stage = StageMaster.query.filter_by(stage_name=stage_name).first()

        if stage is None:
            stage = StageMaster(
                stage_name=stage_name,
                display_order=display_order,
                requires_poc=requires_poc,
                is_closed=False,
                is_won=False,
            )
            db.session.add(stage)
        else:
            stage.display_order = display_order
            stage.requires_poc = requires_poc
            stage.is_closed = False
            stage.is_won = False

        result[stage_name] = stage

    db.session.flush()
    return result


def _ensure_user(full_name, email, role):
    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(SEED_PASSWORD),
            active=True,
            status="APPROVED",
            approved_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.flush()
    else:
        user.full_name = full_name
        user.active = True
        user.status = "APPROVED"

        if user.approved_at is None:
            user.approved_at = datetime.utcnow()

    existing_role = UserRole.query.filter_by(
        user_id=user.user_id,
        role=role,
    ).first()

    if existing_role is None:
        db.session.add(
            UserRole(
                user_id=user.user_id,
                role=role,
            )
        )

    return user


def _ensure_users():
    users = {}

    # Reuse the canonical Leadership seed.
    leadership = User.query.filter_by(
        email="leadership@dataeko.ai"
    ).first()

    if leadership is None:
        leadership = User(
            full_name="System Leadership",
            email="leadership@dataeko.ai",
            password_hash=generate_password_hash(SEED_PASSWORD),
            active=True,
            status="APPROVED",
            approved_at=datetime.utcnow(),
        )
        db.session.add(leadership)
        db.session.flush()

    users[LEADERSHIP] = leadership

    for role, full_name, email in ROLE_USERS:
        users[role] = _ensure_user(full_name, email, role)

    db.session.flush()
    return users


def _ensure_tag(name):
    tag = Tag.query.filter_by(name=name).first()

    if tag is None:
        tag = Tag(
            name=name,
            is_active=True,
        )
        db.session.add(tag)
        db.session.flush()

    else:
        tag.is_active = True

    return tag


def _ensure_tags():
    return {
        name: _ensure_tag(name)
        for name in (
            "Decision Maker",
            "Technical Champion",
            "End User",
            "Blocker",
            "Economic Buyer",
            "Other",
        )
    }


def _ensure_account(account_name, index):
    account = Account.query.filter_by(
        canonical_name=account_name.lower().strip()
    ).first()

    if account is None:
        account = Account(
            account_name=account_name,
            canonical_name=account_name.lower().strip(),
            status="Active",
            industry=[
                "Manufacturing",
                "Healthcare",
                "Financial Services",
                "Retail",
                "Logistics",
                "Technology",
            ][index % 6],
            website=f"https://example.com/ph18/{index}",
            phone=f"+91-90000-{index:05d}",
            country="India",
            state="Telangana",
            city="Hyderabad",
            address=f"Phase 18 Demo Address {index}",
            is_active=True,
        )
        db.session.add(account)
        db.session.flush()

    return account


def _ensure_accounts():
    accounts = []

    for index in range(1, 31):
        account = _ensure_account(
            f"{PREFIX} Account {index:02d}",
            index,
        )
        accounts.append(account)

    return accounts


def _opportunity_spec(index):
    """
    Deterministic lifecycle distribution.

    1-15   Lead
    16-25  Qualified
    26-33  RFX
    34-43  POC
    44-51  Negotiations
    52-56  Delivery
    57-60  Closed Lost examples
    """

    if index <= 15:
        stage = "Lead"
        outcome = "Open"
        operational_status = "Active"
        probability = 10

    elif index <= 25:
        stage = "Qualified"
        outcome = "Open"
        operational_status = "Active"
        probability = 40

    elif index <= 33:
        stage = "RFX"
        outcome = "Open"
        operational_status = "Active"
        probability = 50

    elif index <= 43:
        stage = "POC"
        outcome = "Open"
        operational_status = "Active"
        probability = 60

    elif index <= 51:
        stage = "Negotiations"
        outcome = "Open"
        operational_status = "Active"
        probability = 90

    elif index <= 56:
        stage = "Delivery"
        outcome = "Closed Won"
        operational_status = "Closed"
        probability = 100

    else:
        stage = "Negotiations"
        outcome = "Closed Lost"
        operational_status = "Closed"
        probability = 0

    # Explicit stalled examples among otherwise-open opportunities.
    if index in (5, 20, 29, 39, 47):
        operational_status = "Stalled"

    return stage, outcome, operational_status, probability


def _ensure_opportunity(
    index,
    account,
    users,
    stages,
):
    name = f"{PREFIX} Opportunity {index:03d}"

    opportunity = Opportunity.query.filter_by(
        opportunity_name=name,
        account_id=account.account_id,
    ).first()

    stage_name, outcome, operational_status, probability = _opportunity_spec(index)

    creator_roles = [
        SALES_EXECUTIVE,
        SALES_MANAGER,
        PRE_SALES_MANAGER,
        SOLUTION_ENGINEER,
    ]

    creator = users[creator_roles[(index - 1) % len(creator_roles)]]

    if opportunity is None:
        opportunity = Opportunity(
            account_id=account.account_id,
            created_by=creator.user_id,
            sales_owner_id=users[SALES_EXECUTIVE].user_id,
            stage_id=stages[stage_name].stage_id,
            opportunity_name=name,
            description=f"Phase 18 deterministic demo opportunity {index}.",
            pain_points=(
                f"Demo pain point {index}: improve operational visibility, "
                "reduce manual work, and establish measurable delivery outcomes."
            ),
            estimated_value=Decimal(100000 + index * 25000),
            final_revenue=(
                Decimal(95000 + index * 20000)
                if outcome == "Closed Won"
                else None
            ),
            probability=probability,
            expected_close_date=date.today() + timedelta(days=15 + index),
            lifecycle_stage=stage_name,
            outcome=outcome,
            operational_status=operational_status,
            review_status="Approved",
            lost_reason=(
                "Budget"
                if outcome == "Closed Lost"
                else None
            ),
            lost_explanation=(
                "Phase 18 closed-lost example for workflow testing."
                if outcome == "Closed Lost"
                else None
            ),
            row_version=1,
            status=operational_status if operational_status != "Closed" else "Closed",
            is_active=outcome == "Open",
        )

        db.session.add(opportunity)
        db.session.flush()

    else:
        # Repair only records belonging to the Phase 18 namespace.
        opportunity.stage_id = stages[stage_name].stage_id
        opportunity.lifecycle_stage = stage_name
        opportunity.outcome = outcome
        opportunity.operational_status = operational_status
        opportunity.review_status = "Approved"
        opportunity.probability = probability
        opportunity.is_active = outcome == "Open"

        if outcome == "Closed Won":
            opportunity.final_revenue = Decimal(95000 + index * 20000)
            opportunity.status = "Closed"
        elif outcome == "Closed Lost":
            opportunity.final_revenue = None
            opportunity.status = "Closed"
        else:
            opportunity.final_revenue = None
            opportunity.status = operational_status

    db.session.flush()

    # Permanent Deal Finder / opportunity team.
    team_specs = [
        (creator.user_id, creator.role_names()[0] if creator.role_names() else SALES_EXECUTIVE),
        (users[SALES_MANAGER].user_id, SALES_MANAGER),
        (users[PRE_SALES_MANAGER].user_id, PRE_SALES_MANAGER),
        (users[SOLUTION_ENGINEER].user_id, SOLUTION_ENGINEER),
    ]

    for user_id, role in team_specs:
        exists = OpportunityTeam.query.filter_by(
            opportunity_id=opportunity.opportunity_id,
            user_id=user_id,
            role=role,
        ).first()

        if exists is None:
            db.session.add(
                OpportunityTeam(
                    opportunity_id=opportunity.opportunity_id,
                    user_id=user_id,
                    role=role,
                )
            )

    return opportunity


def _ensure_opportunities(accounts, users, stages):
    opportunities = []

    for index in range(1, 61):
        # Deterministic account distribution:
        # some accounts receive multiple opportunities,
        # while the final accounts may have none.
        account = accounts[(index - 1) % 20]

        opportunity = _ensure_opportunity(
            index=index,
            account=account,
            users=users,
            stages=stages,
        )
        opportunities.append(opportunity)

    db.session.flush()
    return opportunities


def _ensure_stakeholder(opportunity, index, tag):
    name = f"PH18 Contact {opportunity.opportunity_id}-{index}"

    stakeholder = Stakeholder.query.filter_by(
        opportunity_id=opportunity.opportunity_id,
        name=name,
    ).first()

    if stakeholder is None:
        stakeholder = Stakeholder(
            opportunity_id=opportunity.opportunity_id,
            name=name,
            job_title={
                "Decision Maker": "Chief Executive Officer",
                "Technical Champion": "CTO",
                "End User": "Operations Manager",
                "Blocker": "Procurement Lead",
                "Economic Buyer": "Finance Director",
                "Other": "Business Analyst",
            }[tag],
            email=f"ph18.{opportunity.opportunity_id}.{index}@example.com",
            phone=f"+91-91000-{opportunity.opportunity_id:05d}",
            company=opportunity.account.account_name,
            is_decision_maker=(tag == "Decision Maker"),
            notes=f"Phase 18 stakeholder tagged {tag}.",
        )
        db.session.add(stakeholder)
        db.session.flush()

    else:
        stakeholder.is_decision_maker = tag == "Decision Maker"

    return stakeholder


def _seed_stakeholders(opportunities, tags):
    for opportunity in opportunities:
        # Exactly one Decision Maker.
        _ensure_stakeholder(
            opportunity,
            1,
            "Decision Maker",
        )

        # Most opportunities have several stakeholders.
        _ensure_stakeholder(
            opportunity,
            2,
            "Technical Champion",
        )
        _ensure_stakeholder(
            opportunity,
            3,
            "End User",
        )

        if opportunity.opportunity_id % 4 == 0:
            _ensure_stakeholder(
                opportunity,
                4,
                "Blocker",
            )

        if opportunity.opportunity_id % 5 == 0:
            _ensure_stakeholder(
                opportunity,
                5,
                "Economic Buyer",
            )

    db.session.flush()

    # Assign tags through the relationship rather than inventing a second
    # stakeholder-role column.
    for opportunity in opportunities:
        stakeholders = Stakeholder.query.filter_by(
            opportunity_id=opportunity.opportunity_id
        ).all()

        for stakeholder in stakeholders:
            if stakeholder.is_decision_maker:
                tag_names = ["Decision Maker", "Economic Buyer"]
            elif stakeholder.job_title == "CTO":
                tag_names = ["Technical Champion"]
            elif stakeholder.job_title == "Operations Manager":
                tag_names = ["End User"]
            elif stakeholder.job_title == "Procurement Lead":
                tag_names = ["Blocker"]
            else:
                tag_names = ["Other"]

            stakeholder.tags = [
                tags[name]
                for name in tag_names
            ]

    db.session.flush()


def _ensure_rfx(opportunity, user):
    context = RFXContext.query.filter_by(
        opportunity_id=opportunity.opportunity_id
    ).first()

    if context is None:
        context = RFXContext(
            opportunity_id=opportunity.opportunity_id,
            drive_link=(
                f"https://drive.example.com/phase18/rfx/"
                f"{opportunity.opportunity_id}"
            ),
            row_version=1,
            created_by=user.user_id,
        )
        db.session.add(context)

    return context


def _seed_rfx(opportunities, users):
    for opportunity in opportunities:
        if opportunity.lifecycle_stage == "RFX":
            _ensure_rfx(
                opportunity,
                users[PRE_SALES_MANAGER],
            )

    db.session.flush()


def _ensure_poc(opportunity, number, users):
    poc_name = (
        f"{PREFIX} POC {opportunity.opportunity_id}-{number}"
    )

    poc = POCTracker.query.filter_by(
        opportunity_id=opportunity.opportunity_id,
        poc_name=poc_name,
    ).first()

    is_repeat_failure = (
        opportunity.opportunity_name == f"{PREFIX} Opportunity 034"
        and number == 1
    )
    is_repeat_success = (
        opportunity.opportunity_name == f"{PREFIX} Opportunity 034"
        and number == 2
    )

    if is_repeat_failure:
        status = "Completed"
        outcome = "Failure"
    elif is_repeat_success:
        status = "Completed"
        outcome = "Success"
    elif opportunity.opportunity_id % 3 == 0:
        status = "Submitted"
        outcome = "Ongoing"
    else:
        status = "In Progress"
        outcome = None

    if poc is None:
        poc = POCTracker(
            opportunity_id=opportunity.opportunity_id,
            poc_name=poc_name,
            start_date=date.today() - timedelta(days=number * 5),
            end_date=(
                date.today() - timedelta(days=number)
                if status == "Completed"
                else None
            ),
            status=status,
            row_version=1,
            remarks=f"Phase 18 POC {number}.",
            target_date=date.today() + timedelta(days=10 + number),
            outcome=outcome,
            result_view_link=(
                f"https://example.com/phase18/poc-result/"
                f"{opportunity.opportunity_id}/{number}"
                if status in ("Submitted", "Completed")
                else None
            ),
            submission_metadata=(
                {
                    "seed": "phase18",
                    "poc_number": number,
                    "submitted_via": "seed",
                }
                if status in ("Submitted", "Completed")
                else None
            ),
            outcome_notes=(
                "Phase 18 POC failure example."
                if outcome == "Failure"
                else (
                    "Phase 18 POC success example."
                    if outcome == "Success"
                    else (
                        "Phase 18 POC submitted and awaiting final outcome."
                        if status == "Submitted"
                        else None
                    )
                )
            ),
            requested_by=users[PRE_SALES_MANAGER].user_id,
            submitted_by=(
                users[SOLUTION_ENGINEER].user_id
                if status in ("Submitted", "Completed")
                else None
            ),
            submitted_at=(
                datetime.utcnow() - timedelta(days=number)
                if status in ("Submitted", "Completed")
                else None
            ),
        )
        db.session.add(poc)
        db.session.flush()

    return poc


def _seed_pocs(opportunities, users):
    poc_opportunities = [
        opportunity
        for opportunity in opportunities
        if opportunity.lifecycle_stage == "POC"
    ]

    for opportunity in poc_opportunities:
        _ensure_poc(opportunity, 1, users)

    # Repeat POC example:
    # PH18 Opportunity 034 has a failed first POC followed by a successful
    # repeat POC. We identify it by its deterministic seed name, not by the
    # database primary key, because manual data may already occupy any ID.
    repeat_opportunity = next(
        (
            opportunity
            for opportunity in poc_opportunities
            if opportunity.opportunity_name == f"{PREFIX} Opportunity 034"
        ),
        None,
    )

    if repeat_opportunity is not None:
        _ensure_poc(repeat_opportunity, 2, users)

    # Add two additional POCs to provide broader repeat/multiple-POC coverage.
    for seed_number in (39, 43):
        opportunity = next(
            (
                item
                for item in poc_opportunities
                if item.opportunity_name == f"{PREFIX} Opportunity {seed_number:03d}"
            ),
            None,
        )
        if opportunity is not None:
            _ensure_poc(opportunity, 2, users)

    db.session.flush()

    for poc in POCTracker.query.filter(
        POCTracker.opportunity_id.in_(
            [o.opportunity_id for o in poc_opportunities]
        )
    ).all():
        for user, role in (
            (users[DEVOPS_ENGINEER], DEVOPS_ENGINEER),
            (users[DATA_ANALYST], DATA_ANALYST),
        ):
            exists = POCTeamMember.query.filter_by(
                poc_id=poc.poc_id,
                user_id=user.user_id,
            ).first()

            if exists is None:
                db.session.add(
                    POCTeamMember(
                        poc_id=poc.poc_id,
                        user_id=user.user_id,
                        role=role,
                        assigned_by=users[PRE_SALES_MANAGER].user_id,
                    )
                )

    db.session.flush()


def _ensure_poc_history(opportunity, actor, event_type, reason=None):
    query = POCHistory.query.filter_by(
        opportunity_id=opportunity.opportunity_id,
        actor_id=actor.user_id,
        event_type=event_type,
    )

    if reason:
        query = query.filter_by(reason=reason)

    if query.first() is None:
        db.session.add(
            POCHistory(
                opportunity_id=opportunity.opportunity_id,
                actor_id=actor.user_id,
                event_type=event_type,
                reason=reason,
            )
        )


def _seed_poc_history(opportunities, users):
    for opportunity in opportunities:
        if opportunity.lifecycle_stage != "POC":
            continue

        _ensure_poc_history(
            opportunity,
            users[PRE_SALES_MANAGER],
            "POC_STARTED",
        )

        for poc in POCTracker.query.filter_by(
            opportunity_id=opportunity.opportunity_id
        ).all():
            if poc.status in ("Submitted", "Completed"):
                _ensure_poc_history(
                    opportunity,
                    users[SOLUTION_ENGINEER],
                    "POC_SUBMITTED",
                )

    # Explicit repeat request event.
    repeat = next(
        (
            o for o in opportunities
            if o.opportunity_name == f"{PREFIX} Opportunity 034"
        ),
        None,
    )

    if repeat is not None:
        _ensure_poc_history(
            repeat,
            users[PRE_SALES_MANAGER],
            "NEW_POC_REQUESTED",
            reason="Initial POC failed; repeat validation requested.",
        )

    db.session.flush()


def _ensure_negotiation(opportunity, user):
    context = NegotiationContext.query.filter_by(
        opportunity_id=opportunity.opportunity_id
    ).first()

    if context is None:
        context = NegotiationContext(
            opportunity_id=opportunity.opportunity_id,
            nda_suggested=(opportunity.opportunity_id % 2 == 0),
            nda_link=(
                f"https://example.com/phase18/nda/"
                f"{opportunity.opportunity_id}"
                if opportunity.opportunity_id % 2 == 0
                else None
            ),
            msa_link=f"https://example.com/phase18/msa/{opportunity.opportunity_id}",
            sow_link=f"https://example.com/phase18/sow/{opportunity.opportunity_id}",
            notes="Phase 18 negotiation context.",
            row_version=1,
            created_by=user.user_id,
        )
        db.session.add(context)

    return context


def _seed_negotiations(opportunities, users):
    for opportunity in opportunities:
        if opportunity.lifecycle_stage == "Negotiations":
            _ensure_negotiation(
                opportunity,
                users[SALES_MANAGER],
            )

    db.session.flush()


def _ensure_delivery(opportunity, users):
    project = DeliveryProject.query.filter_by(
        opportunity_id=opportunity.opportunity_id
    ).first()

    done = opportunity.opportunity_id % 2 == 0

    if project is None:
        project = DeliveryProject(
            opportunity_id=opportunity.opportunity_id,
            account_id=opportunity.account_id,
            manager_id=users[DELIVERY_MANAGER].user_id,
            status="Done" if done else "Active",
            completed_at=datetime.utcnow() if done else None,
            row_version=1,
        )
        db.session.add(project)
        db.session.flush()

    else:
        project.manager_id = users[DELIVERY_MANAGER].user_id
        project.status = "Done" if done else "Active"
        project.completed_at = datetime.utcnow() if done else None

    for user in (
        users[DEVOPS_ENGINEER],
        users[DATA_ANALYST],
    ):
        exists = DeliveryProjectMember.query.filter_by(
            delivery_project_id=project.delivery_project_id,
            user_id=user.user_id,
        ).first()

        if exists is None:
            db.session.add(
                DeliveryProjectMember(
                    delivery_project_id=project.delivery_project_id,
                    user_id=user.user_id,
                    is_done=done,
                    is_suggested=True,
                    assigned_by=users[DELIVERY_MANAGER].user_id,
                    completed_at=datetime.utcnow() if done else None,
                )
            )

    return project


def _seed_delivery(opportunities, users):
    for opportunity in opportunities:
        if opportunity.lifecycle_stage == "Delivery":
            _ensure_delivery(opportunity, users)

    db.session.flush()


def _ensure_follow_up(opportunity, owner, creator, number):
    description = (
        f"{PREFIX} follow-up {number} for "
        f"opportunity {opportunity.opportunity_id}"
    )

    existing = FollowUp.query.filter_by(
        opportunity_id=opportunity.opportunity_id,
        description=description,
    ).first()

    if existing is not None:
        return existing

    if number % 3 == 0:
        status = "Completed"
        due_date = date.today() - timedelta(days=number + 2)
        completed_at = datetime.utcnow() - timedelta(days=number)
    elif number % 2 == 0:
        status = "Overdue"
        due_date = date.today() - timedelta(days=number + 1)
        completed_at = None
    else:
        status = "Open"
        due_date = date.today() + timedelta(days=number + 2)
        completed_at = None

    follow_up = FollowUp(
        opportunity_id=opportunity.opportunity_id,
        owner_id=owner.user_id,
        description=description,
        due_date=due_date,
        status=status,
        completed_at=completed_at,
        created_by=creator.user_id,
    )

    db.session.add(follow_up)
    db.session.flush()

    return follow_up


def _seed_follow_ups(opportunities, users):
    for index, opportunity in enumerate(opportunities, start=1):
        _ensure_follow_up(
            opportunity,
            users[SALES_EXECUTIVE],
            users[SALES_EXECUTIVE],
            index,
        )

        if index <= 50:
            _ensure_follow_up(
                opportunity,
                users[SOLUTION_ENGINEER],
                users[PRE_SALES_MANAGER],
                index + 100,
            )

    db.session.flush()


def _ensure_activity(opportunity, actor, activity_type, number):
    summary = (
        f"{PREFIX} {activity_type} activity {number} "
        f"for opportunity {opportunity.opportunity_id}"
    )

    existing = Activity.query.filter_by(
        opportunity_id=opportunity.opportunity_id,
        summary=summary,
    ).first()

    if existing is not None:
        return existing

    activity = Activity(
        opportunity_id=opportunity.opportunity_id,
        activity_type=activity_type,
        summary=summary,
        actor_id=actor.user_id,
    )

    db.session.add(activity)
    db.session.flush()

    return activity


def _seed_activities(opportunities, users):
    for index, opportunity in enumerate(opportunities, start=1):
        _ensure_activity(
            opportunity,
            users[SALES_EXECUTIVE],
            "note",
            index,
        )

        _ensure_activity(
            opportunity,
            users[SALES_MANAGER],
            "call",
            index,
        )

        if index <= 20:
            _ensure_activity(
                opportunity,
                users[SOLUTION_ENGINEER],
                "note",
                index + 100,
            )

    db.session.flush()


def _seed_history(opportunities, users, stages):
    for opportunity in opportunities:
        stage = stages[opportunity.lifecycle_stage]

        exists = StageHistory.query.filter_by(
            opportunity_id=opportunity.opportunity_id,
            to_lifecycle_stage=opportunity.lifecycle_stage,
        ).first()

        if exists is None:
            db.session.add(
                StageHistory(
                    opportunity_id=opportunity.opportunity_id,
                    stage_id=stage.stage_id,
                    from_lifecycle_stage=None,
                    to_lifecycle_stage=opportunity.lifecycle_stage,
                    actor_active_role=SALES_MANAGER,
                    version=1,
                    changed_by=users[SALES_MANAGER].user_id,
                    remarks="Phase 18 deterministic seed state.",
                )
            )

        value_exists = OpportunityValueHistory.query.filter_by(
            opportunity_id=opportunity.opportunity_id,
            new_value=opportunity.estimated_value,
        ).first()

        if value_exists is None:
            db.session.add(
                OpportunityValueHistory(
                    opportunity_id=opportunity.opportunity_id,
                    old_value=None,
                    new_value=opportunity.estimated_value,
                    reason="Phase 18 initial seeded opportunity value.",
                    actor_id=users[SALES_EXECUTIVE].user_id,
                    actor_active_role=SALES_EXECUTIVE,
                    opportunity_row_version=opportunity.row_version,
                )
            )

    db.session.flush()


def _delete_demo_children(opportunities):
    """Delete Phase 18 children before deleting Phase 18 opportunities."""
    opportunity_ids = [
        opportunity.opportunity_id
        for opportunity in opportunities
    ]

    if not opportunity_ids:
        return

    pocs = POCTracker.query.filter(
        POCTracker.opportunity_id.in_(opportunity_ids)
    ).all()

    poc_ids = [poc.poc_id for poc in pocs]

    if poc_ids:
        POCTeamMember.query.filter(
            POCTeamMember.poc_id.in_(poc_ids)
        ).delete(synchronize_session=False)

    # POC history is append-only during normal application operation.
    # The explicit --reset-demo path is allowed to remove only Phase 18
    # history records, so temporarily disable the PostgreSQL immutability
    # trigger within this transaction and immediately restore it afterward.
    bind = db.session.get_bind()
    if bind.dialect.name == "postgresql":
        db.session.execute(
            text(
                "ALTER TABLE poc_history DISABLE TRIGGER trg_poc_history_immutable"
            )
        )

    try:
        POCHistory.query.filter(
            POCHistory.opportunity_id.in_(opportunity_ids)
        ).delete(synchronize_session=False)
    finally:
        if bind.dialect.name == "postgresql":
            db.session.execute(
                text(
                    "ALTER TABLE poc_history ENABLE TRIGGER trg_poc_history_immutable"
                )
            )

    POCTracker.query.filter(
        POCTracker.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    Activity.query.filter(
        Activity.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    FollowUp.query.filter(
        FollowUp.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    RFXContext.query.filter(
        RFXContext.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    NegotiationContext.query.filter(
        NegotiationContext.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    projects = DeliveryProject.query.filter(
        DeliveryProject.opportunity_id.in_(opportunity_ids)
    ).all()

    project_ids = [
        project.delivery_project_id
        for project in projects
    ]

    if project_ids:
        DeliveryProjectMember.query.filter(
            DeliveryProjectMember.delivery_project_id.in_(project_ids)
        ).delete(synchronize_session=False)

    DeliveryProject.query.filter(
        DeliveryProject.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    Stakeholder.query.filter(
        Stakeholder.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    OpportunityTeam.query.filter(
        OpportunityTeam.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    StageHistory.query.filter(
        StageHistory.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    OpportunityValueHistory.query.filter(
        OpportunityValueHistory.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    Opportunity.query.filter(
        Opportunity.opportunity_id.in_(opportunity_ids)
    ).delete(synchronize_session=False)

    db.session.flush()


def _reset_demo():
    """Delete only Phase 18 business/demo records."""
    demo_opportunities = Opportunity.query.filter(
        Opportunity.opportunity_name.like(f"{PREFIX}%")
    ).all()

    _delete_demo_children(demo_opportunities)

    demo_accounts = Account.query.filter(
        Account.account_name.like(f"{PREFIX}%")
    ).all()

    for account in demo_accounts:
        # Do not delete an account if it contains a non-Phase18 opportunity.
        remaining = Opportunity.query.filter_by(
            account_id=account.account_id
        ).count()

        if remaining == 0:
            db.session.delete(account)

    # Delete only Phase18 users. Never delete the canonical Leadership seed.
    demo_users = User.query.filter(
        User.email.like("ph18.%@dataeko.ai")
    ).all()

    for user in demo_users:
        db.session.delete(user)

    db.session.flush()
    db.session.commit()


def seed_v2(reset_demo=False):
    """
    Authoritative Phase 18 deterministic development seed.

    The operation is intentionally idempotent.
    Existing non-PH18/manual data is preserved.
    """

    if reset_demo:
        _reset_demo()

    try:
        stages = _ensure_stage_master()
        users = _ensure_users()
        _ensure_tags()

        accounts = _ensure_accounts()
        opportunities = _ensure_opportunities(
            accounts,
            users,
            stages,
        )

        tags = _ensure_tags()
        _seed_stakeholders(opportunities, tags)
        _seed_rfx(opportunities, users)
        _seed_pocs(opportunities, users)
        _seed_poc_history(opportunities, users)
        _seed_negotiations(opportunities, users)
        _seed_delivery(opportunities, users)
        _seed_follow_ups(opportunities, users)
        _seed_activities(opportunities, users)
        _seed_history(opportunities, users, stages)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return {
        "users": 9,
        "accounts": len(accounts),
        "opportunities": len(opportunities),
    }
