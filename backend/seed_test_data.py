"""
Seed realistic test data into the Dealroom PostgreSQL database.

Run from the backend directory:
    python seed_test_data.py

By default this script uses the database configured by DATABASE_URL.
If you want to explicitly choose a connection string, set:
    SEED_DATABASE_URL=postgresql://user:password@localhost:5432/dealroom
"""

import os
from datetime import date, datetime, timedelta
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()

# ---------------------------------------------------------------------------
# Database selection
# ---------------------------------------------------------------------------



# configured_url = os.getenv("SEED_DATABASE_URL") or os.getenv("DATABASE_URL")

# if not configured_url:
#     raise RuntimeError(
#         "DATABASE_URL is not set. Add it to .env or set SEED_DATABASE_URL."
#     )

# # The project .env currently points to dealroom2. This seed script is
# # intentionally pointed at the requested database: dealroom.
# if not os.getenv("SEED_DATABASE_URL"):
#     url = make_url(configured_url)
#     url = url.set(database="dealroom")
#     os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
# else:
#     os.environ["DATABASE_URL"] = configured_url


configured_url = os.getenv("SEED_DATABASE_URL") or os.getenv("DATABASE_URL")

if not configured_url:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to .env or set SEED_DATABASE_URL."
    )

os.environ["DATABASE_URL"] = configured_url



from app import create_app
from app.database import db
from app.auth.password import hash_password
from app.constants.auth_constants import STATUS_APPROVED, STATUS_PENDING, STATUS_REVOKED
from app.constants.roles import ADMIN, PRE_SALES_MANAGER, DELIVERY
from app.models.system.notification import Notification

# This seed script intentionally does NOT create or modify users/roles.

# Import every model that currently has a real table in this project.
from app.models.auth.user import User
from app.models.auth.user_role import UserRole
from app.models.account.account import Account
from app.models.account.contact import Contact
from app.models.account.oem_partner import OEMPartner
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.stage_history import StageHistory
from app.models.opportunity.poc_tracker import POCTracker
from app.models.poc.poc import Poc
from app.models.system.tag import Tag
from app.models.system.audit_log import AuditLog

from app.constants.roles import SALES_EXECUTIVE, SALES_MANAGER, SOLUTION_ENGINEER, DELIVERY
from app.constants.stages import PIPELINE_STAGES, CLOSED_STATUS, OPEN_STATUS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_or_create(model, filters, defaults=None):
    """Return an existing row or create it."""
    obj = model.query.filter_by(**filters).first()
    if obj:
        return obj, False

    values = dict(defaults or {})
    values.update(filters)

    obj = model(**values)
    db.session.add(obj)
    db.session.flush()
    return obj, True


def seed_users():
    """Create/update only the documented local development identities."""
    password_hash = hash_password("Test@123")
    specs = [
        ("System Administrator", "admin@dealroom.local", [ADMIN], STATUS_APPROVED),
        ("Sales Executive", "sales.exec@dealroom.local", [SALES_EXECUTIVE], STATUS_APPROVED),
        ("Sales Manager", "sales.manager@dealroom.local", [SALES_MANAGER], STATUS_APPROVED),
        ("Pre-Sales Manager", "presales.manager@dealroom.local", [PRE_SALES_MANAGER], STATUS_APPROVED),
        ("Solution Engineer", "solution.engineer@dealroom.local", [SOLUTION_ENGINEER], STATUS_APPROVED),
        ("Solution Engineer", "delivery@dealroom.local", [DELIVERY], STATUS_APPROVED),
        ("Multi Role User", "multi.role@dealroom.local", [SOLUTION_ENGINEER], STATUS_APPROVED),
        ("Pending User", "pending@dealroom.local", [], STATUS_PENDING),
        ("Revoked User", "revoked@dealroom.local", [SALES_EXECUTIVE], STATUS_REVOKED),
    ]
    users = {}
    for name, email, roles, status in specs:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(full_name=name, email=email, password_hash=password_hash,
                        status=status, active=(status != STATUS_REVOKED),
                        approved_at=datetime.utcnow() if status == STATUS_APPROVED else None)
            db.session.add(user)
            db.session.flush()
        else:
            user.full_name = name
            user.password_hash = password_hash
            user.status = status
            user.active = status != STATUS_REVOKED
            if status == STATUS_APPROVED and not user.approved_at:
                user.approved_at = datetime.utcnow()
        existing_roles = {row.role for row in user.roles}
        for role in roles:
            if role not in existing_roles:
                user.roles.append(UserRole(role=role))
        if not roles:
            for row in list(user.roles):
                db.session.delete(row)
        users[email.lower()] = user

    db.session.flush()
    manager_map = {
        "sales.exec@dealroom.local": "sales.manager@dealroom.local",
        "solution.engineer@dealroom.local": "presales.manager@dealroom.local",
        "delivery@dealroom.local": "presales.manager@dealroom.local",
        "multi.role@dealroom.local": "presales.manager@dealroom.local",
    }
    for email, manager_email in manager_map.items():
        users[email].manager_id = users[manager_email].user_id
    for email in {"admin@dealroom.local", "sales.manager@dealroom.local",
                  "presales.manager@dealroom.local", "pending@dealroom.local",
                  "revoked@dealroom.local"}:
        users[email].manager_id = None
    db.session.commit()
    print("\nDevelopment users ready:")
    for email, user in users.items():
        print(f"  - {email}: {', '.join(user.role_names()) or 'No role'} [{user.status}]")
    return users


def get_user_for_assignment(users, index):
    """
    Return an existing user for test-data ownership/team assignments.

    The seed data never creates a user or role. If there are fewer users than
    the requested index, cycle through the existing users.
    """
    existing_users = list(users.values())
    if not existing_users:
        raise RuntimeError("No existing users are available for assignment.")

    return existing_users[index % len(existing_users)]

def get_user_by_system_role(users, role):
    """Return an existing user assigned the requested canonical system role."""
    for user in users.values():
        if user.has_role(role):
            return user
    return None


def seed_stages():
    stages = {}

    for stage_data in PIPELINE_STAGES:
        stage, _ = get_or_create(
            StageMaster,
            {"stage_name": stage_data["stage_name"]},
            {
                "display_order": stage_data["display_order"],
                "requires_poc": stage_data["requires_poc"],
                "is_closed": stage_data["stage_name"] in {
                    "Closed Won",
                    "Closed Lost",
                },
                "is_won": stage_data["stage_name"] == "Closed Won",
            },
        )

        # Keep existing rows aligned with the current stage definition.
        stage.display_order = stage_data["display_order"]
        stage.requires_poc = stage_data["requires_poc"]
        stage.is_closed = stage_data["stage_name"] in {
            "Closed Won",
            "Closed Lost",
        }
        stage.is_won = stage_data["stage_name"] == "Closed Won"

        stages[stage.stage_name] = stage

    db.session.flush()
    return stages


def seed_accounts():
    accounts_data = [
        {
            "account_name": "Acme Technologies",
            "industry": "Technology",
            "website": "https://acme.example.com",
            "phone": "+91-9876500001",
            "country": "India",
            "state": "Karnataka",
            "city": "Bengaluru",
            "address": "Outer Ring Road, Bengaluru",
        },
        {
            "account_name": "Nova Pharma",
            "industry": "Pharmaceuticals",
            "website": "https://nova-pharma.example.com",
            "phone": "+91-9876500002",
            "country": "India",
            "state": "Maharashtra",
            "city": "Mumbai",
            "address": "Andheri East, Mumbai",
        },
        {
            "account_name": "FinEdge Bank",
            "industry": "Banking",
            "website": "https://finedge.example.com",
            "phone": "+91-9876500003",
            "country": "India",
            "state": "Telangana",
            "city": "Hyderabad",
            "address": "HITEC City, Hyderabad",
        },
        {
            "account_name": "CloudPeak Systems",
            "industry": "Cloud Computing",
            "website": "https://cloudpeak.example.com",
            "phone": "+91-9876500004",
            "country": "India",
            "state": "Delhi",
            "city": "New Delhi",
            "address": "Connaught Place, New Delhi",
        },
        {
            "account_name": "Global Retail Group",
            "industry": "Retail",
            "website": "https://global-retail.example.com",
            "phone": "+91-9876500005",
            "country": "India",
            "state": "Tamil Nadu",
            "city": "Chennai",
            "address": "Guindy, Chennai",
        },
    ]

    accounts = {}

    for data in accounts_data:
        account, _ = get_or_create(
            Account,
            {"account_name": data["account_name"]},
            data,
        )

        for key, value in data.items():
            setattr(account, key, value)

        accounts[data["account_name"]] = account

    db.session.flush()
    return accounts


def seed_contacts(accounts):
    contacts_data = [
        ("Acme Technologies", "Vikram Malhotra", "CTO", "vikram@acme.example.com", "Decision Maker"),
        ("Acme Technologies", "Neha Rao", "Engineering Director", "neha@acme.example.com", "Influencer"),
        ("Nova Pharma", "Dr. Ananya Iyer", "VP Engineering", "ananya@nova-pharma.example.com", "Decision Maker"),
        ("Nova Pharma", "Rohit Jain", "DevOps Lead", "rohit@nova-pharma.example.com", "User"),
        ("FinEdge Bank", "Karan Shah", "CISO", "karan@finedge.example.com", "Decision Maker"),
        ("CloudPeak Systems", "Meera Nair", "Head of Platform", "meera@cloudpeak.example.com", "Influencer"),
        ("Global Retail Group", "Sahil Bansal", "VP Technology", "sahil@global-retail.example.com", "Decision Maker"),
    ]

    for account_name, name, title, email, _ in contacts_data:
        account = accounts[account_name]

        contact, _ = get_or_create(
            Contact,
            {"account_id": account.account_id, "email": email},
            {
                "full_name": name,
                "title": title,
                "is_primary": True,
            },
        )

        contact.full_name = name
        contact.title = title
        contact.is_primary = True


def seed_oem_partners(accounts):
    partners = [
        ("Nova Pharma", "JFrog", "JFrog Platform", "Partner Team", "partner@jfrog.com"),
        ("FinEdge Bank", "IBM", "IBM Instana", "Partner Team", "partner@ibm.com"),
        ("CloudPeak Systems", "MeshIQ", "MeshIQ Observe", "Partner Team", "partner@meshiq.com"),
        ("Acme Technologies", "AWS", "AWS DevOps", "Partner Team", "partner@aws.example.com"),
    ]

    for account_name, partner_name, product_name, contact_person, email in partners:
        account = accounts[account_name]

        get_or_create(
            OEMPartner,
            {
                "account_id": account.account_id,
                "partner_name": partner_name,
                "product_name": product_name,
            },
            {
                "contact_person": contact_person,
                "email": email,
                "status": "Active",
                "notes": "Seeded test partner.",
            },
        )


def seed_tags():
    tags = [
        ("Enterprise", "#1"),
        ("DevSecOps", "#2"),
        ("High Value", "#3"),
        ("POC", "#4"),
        ("At Risk", "#5"),
        ("Partner", "#6"),
    ]

    for name, color in tags:
        get_or_create(
            Tag,
            {"name": name},
            {"color": color, "is_active": True},
        )


def seed_opportunities(accounts, stages, users):
    opportunities_data = [
        {
            "account": "Acme Technologies",
            "name": "Acme DevSecOps Transformation",
            "stage": "Discovery",
            "value": Decimal("1800000"),
            "probability": 55,
            "status": "Open",
            "days_to_close": 70,
            "description": "Enterprise CI/CD, artifact management and security modernization.",
        },
        {
            "account": "Nova Pharma",
            "name": "Nova Pharma Secure Software Supply Chain",
            "stage": "POC / Technical Evaluation",
            "value": Decimal("4200000"),
            "probability": 70,
            "status": "Open",
            "days_to_close": 45,
            "description": "Secure artifact lifecycle, SBOM and vulnerability governance for regulated workloads.",
        },
        {
            "account": "FinEdge Bank",
            "name": "FinEdge Observability Platform",
            "stage": "Proposal",
            "value": Decimal("3200000"),
            "probability": 65,
            "status": "Open",
            "days_to_close": 35,
            "description": "Application and infrastructure observability rollout.",
        },
        {
            "account": "CloudPeak Systems",
            "name": "CloudPeak Kubernetes Platform",
            "stage": "Qualification",
            "value": Decimal("1500000"),
            "probability": 35,
            "status": "Open",
            "days_to_close": 90,
            "description": "Kubernetes platform engineering and deployment automation.",
        },
        {
            "account": "Global Retail Group",
            "name": "Retail CI/CD Modernization",
            "stage": "Negotiation",
            "value": Decimal("2800000"),
            "probability": 80,
            "status": "Open",
            "days_to_close": 20,
            "description": "Modern CI/CD platform across retail application teams.",
        },
        {
            "account": "Acme Technologies",
            "name": "Acme Cloud Migration Advisory",
            "stage": "Closed Won",
            "value": Decimal("950000"),
            "probability": 100,
            "status": CLOSED_STATUS,
            "days_to_close": -10,
            "description": "Cloud migration advisory and implementation services.",
        },
        {
            "account": "FinEdge Bank",
            "name": "FinEdge Legacy Modernization",
            "stage": "Closed Lost",
            "value": Decimal("2100000"),
            "probability": 0,
            "status": CLOSED_STATUS,
            "days_to_close": -30,
            "description": "Legacy application modernization opportunity.",
        },
        {
            "account": "Nova Pharma",
            "name": "Nova Pharma Platform Expansion",
            "stage": "Lead / Identified",
            "value": Decimal("1100000"),
            "probability": 15,
            "status": "Open",
            "days_to_close": 120,
            "description": "Potential platform expansion for additional engineering teams.",
        },
        {
            "account": "CloudPeak Systems",
            "name": "CloudPeak Security Automation",
            "stage": "Discovery",
            "value": Decimal("2400000"),
            "probability": 50,
            "status": "Open",
            "days_to_close": 75,
            "description": "Security automation and policy enforcement across cloud workloads.",
        },
        {
            "account": "Global Retail Group",
            "name": "Retail Platform POC",
            "stage": "POC / Technical Evaluation",
            "value": Decimal("1700000"),
            "probability": 60,
            "status": "Open",
            "days_to_close": 50,
            "description": "Technical evaluation for a shared engineering platform.",
        },
    ]

    opportunities = {}

    for data in opportunities_data:
        account = accounts[data["account"]]
        stage = stages[data["stage"]]

        opportunity, created = get_or_create(
            Opportunity,
            {
                "account_id": account.account_id,
                "opportunity_name": data["name"],
            },
            {
                "stage_id": stage.stage_id,
                "description": data["description"],
                "estimated_value": data["value"],
                "probability": data["probability"],
                "expected_close_date": date.today() + timedelta(days=data["days_to_close"]),
                "status": data["status"],
                "is_active": data["status"] == OPEN_STATUS,
                "created_by": (
                    get_user_by_system_role(users, SALES_EXECUTIVE).user_id
                    if get_user_by_system_role(users, SALES_EXECUTIVE)
                    else None
                ),
                "sales_owner_id": (
                    get_user_by_system_role(users, SALES_EXECUTIVE).user_id
                    if get_user_by_system_role(users, SALES_EXECUTIVE)
                    else None
                ),
            },
        )

        # Keep reruns deterministic.
        opportunity.stage_id = stage.stage_id
        opportunity.description = data["description"]
        opportunity.estimated_value = data["value"]
        opportunity.probability = data["probability"]
        opportunity.expected_close_date = date.today() + timedelta(days=data["days_to_close"])
        opportunity.status = data["status"]
        opportunity.is_active = data["status"] == OPEN_STATUS
        if opportunity.created_by is None:
            creator = get_user_by_system_role(users, SALES_EXECUTIVE)
            opportunity.created_by = creator.user_id if creator else None
        if opportunity.sales_owner_id is None:
            owner = get_user_by_system_role(users, SALES_EXECUTIVE)
            opportunity.sales_owner_id = owner.user_id if owner else None

        opportunities[data["name"]] = opportunity

        if created:
            db.session.flush()

    # Make one opportunity clearly "stalled" for dashboard testing.
    stalled = opportunities["CloudPeak Security Automation"]
    stalled.created_at = datetime.utcnow() - timedelta(days=35)
    stalled.updated_at = datetime.utcnow() - timedelta(days=21)

    # Make one POC opportunity older enough to exercise ageing.
    pocs = opportunities["Nova Pharma Secure Software Supply Chain"]
    pocs.created_at = datetime.utcnow() - timedelta(days=28)
    pocs.updated_at = datetime.utcnow() - timedelta(days=5)

    db.session.flush()
    return opportunities


def seed_opportunity_teams(opportunities, users):
    """Seed deliberately separated opportunity-team memberships."""
    assignments = [
        ("Acme DevSecOps Transformation", "sales.exec@dealroom.local", SALES_EXECUTIVE),
        ("Acme DevSecOps Transformation", "solution.engineer@dealroom.local", SOLUTION_ENGINEER),
        ("Nova Pharma Secure Software Supply Chain", "sales.manager@dealroom.local", SALES_MANAGER),
        ("Nova Pharma Secure Software Supply Chain", "solution.engineer@dealroom.local", SOLUTION_ENGINEER),
        ("Nova Pharma Secure Software Supply Chain", "delivery@dealroom.local", DELIVERY),
        ("FinEdge Observability Platform", "sales.exec@dealroom.local", SALES_EXECUTIVE),
        ("FinEdge Observability Platform", "delivery@dealroom.local", DELIVERY),
        ("CloudPeak Kubernetes Platform", "sales.manager@dealroom.local", SALES_MANAGER),
        ("Global Retail Group", "sales.manager@dealroom.local", SALES_MANAGER),
        ("Retail CI/CD Modernization", "solution.engineer@dealroom.local", SOLUTION_ENGINEER),
        ("Retail CI/CD Modernization", "delivery@dealroom.local", DELIVERY),
    ]
    for opportunity_name, email, team_role in assignments:
        opportunity = opportunities.get(opportunity_name)
        user = users.get(email)
        if not opportunity or not user:
            continue
        existing = OpportunityTeam.query.filter_by(
            opportunity_id=opportunity.opportunity_id,
            user_id=user.user_id,
        ).first()
        if existing:
            existing.role = team_role
        else:
            db.session.add(OpportunityTeam(
                opportunity_id=opportunity.opportunity_id,
                user_id=user.user_id,
                role=team_role,
            ))
    db.session.flush()


def seed_stakeholders(opportunities):
    stakeholders = [
        ("Acme DevSecOps Transformation", "Vikram Malhotra", "CTO", "vikram@acme.example.com", "Decision Maker"),
        ("Acme DevSecOps Transformation", "Neha Rao", "Engineering Director", "neha@acme.example.com", "Influencer"),
        ("Nova Pharma Secure Software Supply Chain", "Dr. Ananya Iyer", "VP Engineering", "ananya@nova-pharma.example.com", "Decision Maker"),
        ("Nova Pharma Secure Software Supply Chain", "Rohit Jain", "DevOps Lead", "rohit@nova-pharma.example.com", "User"),
        ("FinEdge Observability Platform", "Karan Shah", "CISO", "karan@finedge.example.com", "Decision Maker"),
        ("CloudPeak Kubernetes Platform", "Meera Nair", "Head of Platform", "meera@cloudpeak.example.com", "Influencer"),
        ("Retail CI/CD Modernization", "Sahil Bansal", "VP Technology", "sahil@global-retail.example.com", "Decision Maker"),
        ("Retail CI/CD Modernization", "Pooja Verma", "Engineering Manager", "pooja@global-retail.example.com", "User"),
    ]

    for opportunity_name, name, designation, email, influence in stakeholders:
        opportunity = opportunities[opportunity_name]

        get_or_create(
            Stakeholder,
            {
                "opportunity_id": opportunity.opportunity_id,
                "email": email,
            },
            {
                "stakeholder_name": name,
                "designation": designation,
                "phone": "+91-9000000000",
                "influence_level": influence,
                "notes": "Seeded stakeholder for frontend/API testing.",
            },
        )


def seed_stage_history(opportunities, stages, users):
    history_data = [
        (
            "Acme DevSecOps Transformation",
            "Lead / Identified",
            "Lead created from initial account research.",
            0,
        ),
        (
            "Acme DevSecOps Transformation",
            "Qualification",
            "Initial business qualification completed.",
            1,
        ),
        (
            "Acme DevSecOps Transformation",
            "Discovery",
            "Technical and business discovery completed.",
            2,
        ),
        (
            "Nova Pharma Secure Software Supply Chain",
            "Discovery",
            "Regulated software supply-chain requirements gathered.",
            3,
        ),
        (
            "Nova Pharma Secure Software Supply Chain",
            "POC / Technical Evaluation",
            "POC approved by technical stakeholders.",
            0,
        ),
        (
            "Acme Cloud Migration Advisory",
            "Closed Won",
            "Customer accepted the commercial proposal.",
            1,
        ),
        (
            "FinEdge Legacy Modernization",
            "Closed Lost",
            "Customer selected an alternate modernization partner.",
            2,
        ),
    ]

    for opportunity_name, stage_name, remarks, user_index in history_data:
        opportunity = opportunities[opportunity_name]
        stage = stages[stage_name]
        user = get_user_for_assignment(users, user_index)

        exists = StageHistory.query.filter_by(
            opportunity_id=opportunity.opportunity_id,
            stage_id=stage.stage_id,
            remarks=remarks,
        ).first()

        if not exists:
            db.session.add(
                StageHistory(
                    opportunity_id=opportunity.opportunity_id,
                    stage_id=stage.stage_id,
                    changed_by=user.user_id,
                    remarks=remarks,
                )
            )

def seed_pocs(opportunities):
    """Seed POCs using the canonical Phase 6 status vocabulary."""
    poc_data = [
        ("Acme DevSecOps Transformation", "Draft POC", "Draft"),
        ("Nova Pharma Secure Software Supply Chain", "Secure Supply Chain POC", "Draft"),
        ("FinEdge Observability Platform", "Observability POC", "Draft"),
        ("CloudPeak Security Automation", "Security Automation POC", "In Progress"),
        ("Retail Platform POC", "Retail Platform Technical POC", "Submitted"),
        ("CloudPeak Kubernetes Platform", "Completed Kubernetes POC", "Completed"),
    ]
    for opportunity_name, poc_name, status in poc_data:
        opportunity = opportunities[opportunity_name]
        target = date.today() + timedelta(days=20)
        tracker, _ = get_or_create(
            POCTracker,
            {"opportunity_id": opportunity.opportunity_id, "poc_name": poc_name},
            {
                "start_date": date.today(),
                "end_date": target,
                "status": status,
                "remarks": "Seeded POC for local workflow testing.",
                "objective": "Validate the proposed technical solution against agreed requirements.",
                "success_metric": "All mandatory acceptance criteria pass.",
                "target_date": target,
                "failure_condition": "A critical acceptance criterion fails.",
                "outcome": "Success" if status == "Completed" else None,
                "outcome_notes": "Seeded completed result." if status == "Completed" else None,
                "exit_criteria": "Acceptance criteria reviewed and documented.",
            },
        )
        tracker.start_date = date.today()
        tracker.end_date = target
        tracker.status = status
        tracker.objective = "Validate the proposed technical solution against agreed requirements."
        tracker.success_metric = "All mandatory acceptance criteria pass."
        tracker.target_date = target
        tracker.failure_condition = "A critical acceptance criterion fails."
        tracker.outcome = "Success" if status == "Completed" else None
        tracker.outcome_notes = "Seeded completed result." if status == "Completed" else None
        tracker.exit_criteria = "Acceptance criteria reviewed and documented."
        db.session.flush()


def seed_legacy_poc_table(opportunities):
    """
    The project also has a separate `poc` model/table. It is not linked with
    a SQL foreign key, so seed one row for testing its API independently.
    """
    opportunity = opportunities["Nova Pharma Secure Software Supply Chain"]

    existing = Poc.query.filter_by(
        opportunity_id=opportunity.opportunity_id
    ).first()

    if not existing:
        db.session.add(
            Poc(
                opportunity_id=opportunity.opportunity_id,
                objective="Validate the core security workflow.",
                success_metric="All critical POC test cases pass.",
                target_date=date.today() + timedelta(days=15),
                failure_condition="Any critical acceptance criterion fails.",
                stakeholder_signoff=False,
                outcome="Ongoing",
                outcome_notes="Seeded legacy POC row.",
            )
        )


def seed_audit_logs(opportunities, users):
    audit_data = [
        (
            "Opportunity",
            "Acme DevSecOps Transformation",
            "CREATE_OPPORTUNITY",
            "Seeded opportunity for dashboard and API testing.",
            0,
        ),
        (
            "Opportunity",
            "Nova Pharma Secure Software Supply Chain",
            "POC_STARTED",
            "Seeded active POC for frontend testing.",
            1,
        ),
        (
            "Account",
            "Nova Pharma",
            "ACCOUNT_CREATED",
            "Seeded account for account-management testing.",
            2,
        ),
    ]

    for entity_type, entity_name, action, description, user_index in audit_data:
        if entity_type == "Opportunity":
            entity_id = opportunities[entity_name].opportunity_id
        else:
            account = Account.query.filter_by(
                account_name=entity_name
            ).first()

            if not account:
                continue

            entity_id = account.account_id

        exists = AuditLog.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
        ).first()

        if not exists:
            db.session.add(
                AuditLog(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action=action,
                    description=description,
                    performed_by=get_user_for_assignment(
                        users, user_index
                    ).user_id,
                )
            )

def seed_notifications(opportunities, users):
    """Create deterministic in-app workflow examples without duplicates."""
    samples = [
        ("sales.manager@dealroom.local", "OPPORTUNITY_SUBMITTED_FOR_REVIEW", "Opportunity", "Acme DevSecOps Transformation", "Acme DevSecOps Transformation is ready for Sales Manager review."),
        ("presales.manager@dealroom.local", "OPPORTUNITY_APPROVED", "Opportunity", "Nova Pharma Secure Software Supply Chain", "Nova Pharma Secure Software Supply Chain was approved and is ready for technical assignment."),
        ("solution.engineer@dealroom.local", "SOLUTION_ENGINEER_ASSIGNED", "Opportunity", "Nova Pharma Secure Software Supply Chain", "You were assigned as Solution Engineer."),
        ("delivery@dealroom.local", "SOLUTION_ENGINEER_ASSIGNED", "Opportunity", "Nova Pharma Secure Software Supply Chain", "You were assigned for Delivery/POC execution."),
        ("presales.manager@dealroom.local", "POC_REQUESTED", "POC", "Secure Supply Chain POC", "A Solution Engineer requested POC approval."),
        ("delivery@dealroom.local", "POC_APPROVED", "POC", "Observability Approval POC", "The POC was approved for execution."),
        ("solution.engineer@dealroom.local", "POC_RESULT_SUBMITTED", "POC", "Retail Platform Technical POC", "Delivery submitted a POC result for review."),
    ]
    for email, kind, entity_type, name, message in samples:
        user = users.get(email)
        if not user:
            continue
        if entity_type == "Opportunity":
            entity = opportunities.get(name)
            entity_id = entity.opportunity_id if entity else None
        else:
            entity = POCTracker.query.filter_by(poc_name=name).first()
            entity_id = entity.poc_id if entity else None
        if entity_id is None:
            continue
        exists = Notification.query.filter_by(
            recipient_user_id=user.user_id,
            notification_type=kind,
            entity_type=entity_type,
            entity_id=entity_id,
        ).first()
        if not exists:
            db.session.add(Notification(
                recipient_user_id=user.user_id,
                notification_type=kind,
                entity_type=entity_type,
                entity_id=entity_id,
                message=message,
                is_read=False,
            ))

def main():
    app = create_app()

    with app.app_context():
        print("Seeding Dealroom test data...")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")

        users = seed_users()
        stages = seed_stages()
        accounts = seed_accounts()
        seed_contacts(accounts)
        seed_oem_partners(accounts)
        seed_tags()

        opportunities = seed_opportunities(accounts, stages, users)
        seed_opportunity_teams(opportunities, users)
        seed_stakeholders(opportunities)
        seed_stage_history(opportunities, stages, users)
        seed_pocs(opportunities)
        seed_legacy_poc_table(opportunities)
        seed_audit_logs(opportunities, users)
        seed_notifications(opportunities, users)

        db.session.commit()

        print("\nSeed completed successfully.")
        print(f"  Existing users: {User.query.count()}")
        print(f"  Existing roles: {UserRole.query.count()}")
        print(f"  Stages:        {StageMaster.query.count()}")
        print(f"  Accounts:      {Account.query.count()}")
        print(f"  Contacts:      {Contact.query.count()}")
        print(f"  OEM partners:  {OEMPartner.query.count()}")
        print(f"  Tags:          {Tag.query.count()}")
        print(f"  Opportunities: {Opportunity.query.count()}")
        print(f"  Team members:  {OpportunityTeam.query.count()}")
        print(f"  Stakeholders:  {Stakeholder.query.count()}")
        print(f"  Stage history: {StageHistory.query.count()}")
        print(f"  POC trackers:  {POCTracker.query.count()}")
        print(f"  POC rows:      {Poc.query.count()}")
        print(f"  Audit logs:    {AuditLog.query.count()}")

        print("\nExisting users used for test-data assignments:")
        for user in users.values():
            print(f"  {user.email}")


if __name__ == "__main__":
    main()