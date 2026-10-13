from app import create_app
from app.models.auth.user import User
from app.services.opportunity_service import OpportunityService

app = create_app()

with app.app_context():
    manager = User.query.filter_by(user_id=3).first()

    opportunity = OpportunityService.review_opportunity(
        opportunity_id=1,
        decision="APPROVE",
        sales_owner_id=2,
        reason=None,
        expected_version=2,
        user=manager,
        active_role="Sales Manager",
        editable_fields={},
    )

    print(
        opportunity.opportunity_id,
        opportunity.lifecycle_stage,
        opportunity.review_status,
        opportunity.outcome,
        opportunity.operational_status,
        opportunity.sales_owner_id,
        opportunity.row_version,
    )
