from app.constants.roles import SALES_EXECUTIVE
from app.constants.stages import INITIAL_STAGE_NAME, OPEN_STATUS
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster


def seed_opportunities():
    if Opportunity.query.first():
        return

    account = Account.query.filter_by(account_id=2).first() or Account.query.first()
    sales_user = User.query.filter(
        User.active.is_(True),
        User.status == "APPROVED",
        User.roles.any(role=SALES_EXECUTIVE),
    ).first()
    stage = StageMaster.query.filter_by(stage_name=INITIAL_STAGE_NAME).first()

    if not account or not sales_user or not stage:
        print("Skipping opportunity seed: account, Sales Executive, or initial stage is missing.")
        return

    opportunity = Opportunity(
        account_id=account.account_id,
        created_by=sales_user.user_id,
        stage_id=stage.stage_id,
        opportunity_name="JFrog Enterprise Rollout",
        description="Enterprise DevSecOps implementation",
        estimated_value=2500000,
        probability=40,
        status=OPEN_STATUS,
        is_active=True,
    )
    db.session.add(opportunity)
    db.session.flush()
    db.session.add(OpportunityTeam(
        opportunity_id=opportunity.opportunity_id,
        user_id=sales_user.user_id,
        role=SALES_EXECUTIVE,
    ))
    db.session.commit()
