"""Compatibility test-data entry point; uses the canonical V2 reset/seed path."""
from app import create_app
from app.seed.seed_v2 import seed_v2

app = create_app({"TESTING": True})
with app.app_context():
    seed_v2(reset_demo=True)
print("V2 test/demo data reset and seeded.")
