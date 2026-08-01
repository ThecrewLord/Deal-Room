from app.database import db
from app.models.opportunity.opportunity import Opportunity


def seed_opportunities():

    if Opportunity.query.first():
        return

    opportunity = Opportunity(

        account_id=1,

        stage_id=1,

        opportunity_name="JFrog Enterprise Rollout",

        description="Enterprise DevSecOps implementation",

        estimated_value=2500000,

        probability=40,

        status="Open",

        is_active=True,
    )

    db.session.add(opportunity)

    db.session.commit()