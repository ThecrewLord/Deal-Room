from app import create_app
from app.database import db
from app.models.auth.user import User
from app.models.opportunity.opportunity import Opportunity
from app.services.opportunity_service import OpportunityService

app = create_app()

with app.app_context():
    user = db.session.get(User, 2)

    opportunities = [
        (1, "Nair Robotics Volume Supply Agreement", 347000),
        (1, "Nair Robotics Automation Expansion", 520000),
        (2, "Tata Aerospace Systems Integration", 850000),
        (2, "Tata Defense Platform Upgrade", 1250000),
        (3, "Bharat Electronics Manufacturing Solution", 675000),
        (3, "Bharat Electronics Digital Inspection", 425000),
        (4, "Mahindra Connected Factory Program", 950000),
        (4, "Mahindra Robotics Deployment", 580000),
        (5, "Astra Engineering Automation Project", 390000),
        (5, "Astra Engineering Quality Platform", 720000),
    ]

    for account_id, name, value in opportunities:
        OpportunityService.create_opportunity(
            {
                "account_id": account_id,
                "opportunity_name": name,
                "description": f"Fresh V2 opportunity for {name}.",
                "pain_points": "Process efficiency and operational visibility improvement.",
                "estimated_value": value,
                "probability": 10,
            },
            user,
            "Sales Executive",
        )

    print("Opportunities created:", Opportunity.query.count())
