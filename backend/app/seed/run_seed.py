from app import create_app

from app.seed.seed_users import seed_users
from app.seed.seed_stage_master import seed_stage_master
from app.seed.seed_accounts import seed_accounts
from app.seed.seed_opportunities import seed_opportunities
from app.seed.seed_stakeholders import seed_stakeholders
from app.seed.seed_poc import seed_poc
from app.seed.seed_oem import seed_oem


app = create_app()


with app.app_context():

    seed_users()
    seed_stage_master()
    seed_accounts()
    seed_opportunities()
    seed_stakeholders()
    seed_poc()
    seed_oem()


print("Database seed completed successfully.")