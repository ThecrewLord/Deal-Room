from app import create_app

from app.seed.seed_opportunities import seed_opportunities
from app.seed.seed_admin import seed_admin

app = create_app()

with app.app_context():
    seed_admin()
    seed_opportunities()

print("Database seeded successfully.")




# 
#  from app import create_app

# from app.seed.seed_opportunities import seed_opportunities
# from app.seed.seed_admin import seed_admin

# app = create_app()

# with app.app_context():
#     seed_admin()
#     seed_opportunities()

# print("Database seeded successfully.")