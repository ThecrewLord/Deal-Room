from app.constants.roles import SALES_EXECUTIVE
from app.constants.stages import INITIAL_STAGE_NAME
from app.database import db
from app.models.account.account import Account
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.opportunity_team import OpportunityTeam
from app.models.opportunity.stage_master import StageMaster


def seed_opportunities(reset=False):
    if reset:
        db.session.query(Opportunity).delete(synchronize_session=False)
        db.session.commit()
    if Opportunity.query.first():
        return
    account = Account.query.filter_by(account_id=2).first() or Account.query.first()
    sales_user = User.query.filter(User.active.is_(True), User.status == "APPROVED", User.roles.any(role=SALES_EXECUTIVE)).first()
    stage = StageMaster.query.filter_by(stage_name=INITIAL_STAGE_NAME).first()
    if not account or not sales_user or not stage:
        print("Skipping opportunity seed: account, Sales Executive, or V2 Lead stage is missing.")
        return
    opportunity = Opportunity(
        account_id=account.account_id, created_by=sales_user.user_id, stage_id=stage.stage_id,
        opportunity_name="V2 Demo Lead", description="Demo lead awaiting review.",
        pain_points="Demo pain point", estimated_value=2500000, probability=40,
        lifecycle_stage="Lead", outcome="Open", operational_status="Active",
        review_status="Draft", row_version=1, status="Active", is_active=True,
    )
    db.session.add(opportunity); db.session.flush()
    db.session.add(OpportunityTeam(opportunity_id=opportunity.opportunity_id, user_id=sales_user.user_id, role=SALES_EXECUTIVE))
    db.session.commit()
