"""CLI for the single authoritative V2 development seed/reset path."""
import argparse
from app import create_app
from app.seed.seed_admin import seed_admin
from app.seed.seed_v2 import seed_v2

parser = argparse.ArgumentParser()
parser.add_argument("--reset-demo", action="store_true", help="Delete disposable business/demo data; never use against production")
args = parser.parse_args()

app = create_app()
with app.app_context():
    seed_admin()
    seed_v2(reset_demo=args.reset_demo)
print("V2 development seed completed.")
