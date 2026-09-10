"""Compatibility entry point; delegates to the canonical V2 seed path."""
from app import create_app
from app.seed.seed_admin import seed_admin
from app.seed.seed_v2 import seed_v2

app = create_app()
with app.app_context():
    seed_admin()
    seed_v2()
print("Database seeded successfully using the canonical V2 seed path.")
