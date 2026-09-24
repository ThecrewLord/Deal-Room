"""Single authoritative Deal Room V2 development seed/reset implementation."""
from app.database import db
from app.seed.reset_v2_demo import reset_v2_demo_data
from app.seed.seed_stage_master import seed_stage_master
from app.seed.seed_opportunities import seed_opportunities
from app.seed.seed_phase2 import seed_phase2


def seed_v2(reset_demo=False):
    if reset_demo:
        reset_v2_demo_data()
    seed_stage_master()
    seed_opportunities()
    seed_phase2()
    db.session.commit()
