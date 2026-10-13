from app import create_app
from app.models.auth.user import User
from app.services.opportunity_service import OpportunityService

app = create_app()

with app.app_context():
    user = User.query.filter_by(user_id=2).first()

    opportunity = OpportunityService.submit_for_sales_manager_review(
        opportunity_id=1,
        user=user,
        active_role="Sales Executive",
        expected_version=1,
    )

    print(
        opportunity.opportunity_id,
        opportunity.lifecycle_stage,
        opportunity.review_status,
        opportunity.row_version,
    )
