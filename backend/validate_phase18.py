from collections import Counter

from app import create_app
from app.database import db
from app.constants.roles import (
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
from app.models.account.account import Account
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.stakeholder import Stakeholder
from app.models.opportunity.poc_tracker import POCTracker
from app.models.opportunity.poc_history import POCHistory
from app.models.opportunity.stage_history import StageHistory
from app.models.opportunity.opportunity_value_history import (
    OpportunityValueHistory,
)
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

EXPECTED_USERS = {
    "ph18.admin@dataeko.ai": ADMIN,
    "ph18.sales.manager@dataeko.ai": SALES_MANAGER,
    "ph18.sales.executive@dataeko.ai": SALES_EXECUTIVE,
    "ph18.pre.sales@dataeko.ai": PRE_SALES_MANAGER,
    "ph18.solution.engineer@dataeko.ai": SOLUTION_ENGINEER,
    "ph18.delivery.manager@dataeko.ai": DELIVERY_MANAGER,
    "ph18.devops@dataeko.ai": DEVOPS_ENGINEER,
    "ph18.data.analyst@dataeko.ai": DATA_ANALYST,
}

EXPECTED_STAGES = [
    "Lead",
    "Qualified",
    "RFX",
    "POC",
    "Negotiations",
    "Delivery",
]


checks = []


def check(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    checks.append((status, name, details))
    print(f"[{status}] {name}")
    if details:
        print(f"       {details}")


def main():
    app = create_app()

    with app.app_context():
        # Phase 18 demo records are identified by their PH18- names.
        accounts = Account.query.filter(
            Account.account_name.like(f"{PREFIX}%")
        ).all()

        opportunities = Opportunity.query.filter(
            Opportunity.opportunity_name.like(f"{PREFIX}%")
        ).all()

        opportunity_ids = {
            opportunity.opportunity_id
            for opportunity in opportunities
        }

        account_ids = {
            account.account_id
            for account in accounts
        }

        pocs = POCTracker.query.filter(
            POCTracker.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        poc_ids = {poc.poc_id for poc in pocs}

        stakeholders = Stakeholder.query.filter(
            Stakeholder.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        rfx = RFXContext.query.filter(
            RFXContext.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        negotiations = NegotiationContext.query.filter(
            NegotiationContext.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        projects = DeliveryProject.query.filter(
            DeliveryProject.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        activities = Activity.query.filter(
            Activity.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        followups = FollowUp.query.filter(
            FollowUp.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        poc_history = POCHistory.query.filter(
            POCHistory.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        stage_history = StageHistory.query.filter(
            StageHistory.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        value_history = OpportunityValueHistory.query.filter(
            OpportunityValueHistory.opportunity_id.in_(opportunity_ids)
        ).all() if opportunity_ids else []

        poc_team = POCTeamMember.query.filter(
            POCTeamMember.poc_id.in_(poc_ids)
        ).all() if poc_ids else []

        project_ids = {project.delivery_project_id for project in projects}

        delivery_members = DeliveryProjectMember.query.filter(
            DeliveryProjectMember.delivery_project_id.in_(project_ids)
        ).all() if project_ids else []

        # 1. Main record counts
        check("30 Phase 18 accounts", len(accounts) == 30,
              f"Found {len(accounts)}")

        check("60 Phase 18 opportunities", len(opportunities) == 60,
              f"Found {len(opportunities)}")

        check("13 Phase 18 POCs", len(pocs) == 13,
              f"Found {len(pocs)}")

        check("15 Phase 18 POC history events", len(poc_history) == 15,
              f"Found {len(poc_history)}")

        check("207 Phase 18 stakeholders", len(stakeholders) == 207,
              f"Found {len(stakeholders)}")

        check("8 Phase 18 RFX contexts", len(rfx) == 8,
              f"Found {len(rfx)}")

        check("12 Phase 18 negotiation contexts",
              len(negotiations) == 12,
              f"Found {len(negotiations)}")

        check("5 Phase 18 delivery projects", len(projects) == 5,
              f"Found {len(projects)}")

        check("140 Phase 18 activities", len(activities) == 140,
              f"Found {len(activities)}")

        check("110 Phase 18 follow-ups", len(followups) == 110,
              f"Found {len(followups)}")

        # 2. Phase 18 users and roles
        users_ok = True
        user_details = []

        for email, expected_role in EXPECTED_USERS.items():
            user = User.query.filter_by(email=email).first()

            if user is None:
                users_ok = False
                user_details.append(f"Missing {email}")
                continue

            roles = {role.role for role in user.roles}

            if not user.active or user.status != "APPROVED":
                users_ok = False
                user_details.append(
                    f"{email}: active={user.active}, status={user.status}"
                )

            if expected_role not in roles:
                users_ok = False
                user_details.append(
                    f"{email}: expected role {expected_role}, got {roles}"
                )

        check("All 8 Phase 18 users are active, approved, and correctly roled",
              users_ok,
              "; ".join(user_details) if user_details else "All verified")

        # 3. Lifecycle stages
        stage_names = {
            stage.stage_name
            for stage in StageMaster.query.all()
        }

        check("All six lifecycle stages exist",
              set(EXPECTED_STAGES).issubset(stage_names),
              f"Found: {sorted(stage_names)}")

        # 4. Opportunity lifecycle distribution
        stage_counts = Counter(
            opportunity.lifecycle_stage
            for opportunity in opportunities
        )

        expected_stage_counts = {
            "Lead": 15,
            "Qualified": 10,
            "RFX": 8,
            "POC": 10,
            "Negotiations": 12,
            "Delivery": 5,
        }

        check("Opportunity lifecycle distribution matches seed",
              dict(stage_counts) == expected_stage_counts,
              f"Found: {dict(stage_counts)}")

        # 5. Opportunity-account integrity
        check("Every Phase 18 opportunity belongs to an account",
              all(op.account_id is not None for op in opportunities))

        check("Every Phase 18 opportunity references an existing account",
              all(op.account_id in account_ids for op in opportunities),
              "Checks Phase 18 account ownership")

        # 6. Stakeholder integrity
        decision_makers = Counter(
            stakeholder.opportunity_id
            for stakeholder in stakeholders
            if stakeholder.is_decision_maker
        )

        check("No opportunity has multiple Decision Makers",
              all(count <= 1 for count in decision_makers.values()),
              f"Decision Maker opportunities: {len(decision_makers)}")

        check("Every stakeholder belongs to a Phase 18 opportunity",
              all(s.opportunity_id in opportunity_ids for s in stakeholders))

        # 7. POC integrity
        check("Every Phase 18 POC has a target date",
              all(poc.target_date is not None for poc in pocs))

        check("Submitted/completed POCs have a result link",
              all(
                  poc.result_view_link
                  for poc in pocs
                  if poc.status in ("Submitted", "Completed")
              ))

        check("POCs use only allowed statuses",
              all(
                  poc.status in ("Draft", "In Progress", "Submitted", "Completed")
                  for poc in pocs
              ))

        check("POCs use only allowed outcomes",
              all(
                  poc.outcome in (None, "Success", "Failure", "Ongoing", "Abandoned")
                  for poc in pocs
              ))

        check("POC team roles are valid",
              all(
                  member.role in (DEVOPS_ENGINEER, DATA_ANALYST)
                  for member in poc_team
              ),
              f"Found {len(poc_team)} POC team memberships")

        # 8. RFX and Negotiations context integrity
        rfx_ids = {item.opportunity_id for item in rfx}
        negotiation_ids = {
            item.opportunity_id for item in negotiations
        }

        check("RFX contexts belong only to RFX-stage opportunities",
              all(
                  op.lifecycle_stage == "RFX"
                  for op in opportunities
                  if op.opportunity_id in rfx_ids
              ))

        check("Negotiation contexts belong only to Negotiations-stage opportunities",
              all(
                  op.lifecycle_stage == "Negotiations"
                  for op in opportunities
                  if op.opportunity_id in negotiation_ids
              ))

        # 9. Delivery integrity
        check("Delivery projects belong only to Delivery-stage opportunities",
              all(
                  op.lifecycle_stage == "Delivery"
                  for op in opportunities
                  if op.opportunity_id in {
                      project.opportunity_id for project in projects
                  }
              ))

        check("Delivery projects have valid statuses",
              all(project.status in ("Active", "Done") for project in projects))

        check("Delivery team memberships exist",
              len(delivery_members) > 0,
              f"Found {len(delivery_members)}")

        # 10. Activities and follow-ups
        check("Activities use valid types",
              all(
                  activity.activity_type in ("note", "call")
                  for activity in activities
              ))

        check("Follow-ups use valid statuses",
              all(
                  followup.status in ("Open", "Overdue", "Completed")
                  for followup in followups
              ))

        # 11. History records
        check("Every opportunity has stage history",
              all(
                  any(h.opportunity_id == op.opportunity_id for h in stage_history)
                  for op in opportunities
              ))

        check("Every opportunity has value history",
              all(
                  any(h.opportunity_id == op.opportunity_id for h in value_history)
                  for op in opportunities
              ))

        # Summary
        print("\n" + "=" * 60)
        passed = sum(status == "PASS" for status, _, _ in checks)
        failed = sum(status == "FAIL" for status, _, _ in checks)

        print(f"Phase 18 validation complete: {passed} PASS, {failed} FAIL")
        print("=" * 60)

        if failed:
            print("\nFailed checks:")
            for status, name, details in checks:
                if status == "FAIL":
                    print(f"- {name}" + (f": {details}" if details else ""))

        # No commit, delete, seed, or update operations are performed.
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
