"""Authoritative Deal Room V2 seed path."""
from app import create_app
from app.database import db
from app.seed.seed_admin import seed_admin
from app.seed.seed_stage_master import seed_stage_master
from app.seed.seed_opportunities import seed_opportunities

app = create_app()

with app.app_context():
    seed_admin()
    seed_stage_master()
    seed_opportunities()
    db.session.commit()

print("Database seeded successfully using the canonical V2 seed path.")
