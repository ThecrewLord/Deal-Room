from app import create_app
from app.seed.seed_opportunities import seed_opportunities

app = create_app()

with app.app_context():
    seed_opportunities()

print("Opportunity seed completed successfully.")