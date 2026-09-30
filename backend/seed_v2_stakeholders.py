from app import create_app
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.services.stakeholder_service import StakeholderService

app = create_app()

with app.app_context():
    user = User.query.filter_by(user_id=2).first()

    opportunities = Opportunity.query.order_by(
        Opportunity.opportunity_id
    ).all()

    for opp in opportunities:
        existing = opp.stakeholders

        if existing:
            print(f"SKIP: Opportunity {opp.opportunity_id} already has stakeholder")
            continue

        stakeholder = StakeholderService.create_stakeholder(
            {
                "opportunity_id": opp.opportunity_id,
                "name": f"{opp.account.account_name} Decision Maker",
                "job_title": "Business Head",
                "email": f"decision.maker{opp.opportunity_id}@example.com",
                "company": opp.account.account_name,
                "notes": "V2 test stakeholder for Lead review workflow.",
                "tags": ["Decision Maker"],
            },
            user,
            "Sales Executive",
        )

        print(
            f"CREATED: Opportunity {opp.opportunity_id} -> "
            f"{stakeholder.name}"
        )

    print("\nStakeholder count:", len(
        Opportunity.query.all()[0].stakeholders
    ))
