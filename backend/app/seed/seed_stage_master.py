from app.constants.stages import PIPELINE_STAGES
from app.database import db
from app.models.opportunity.stage_master import StageMaster


def seed_stage_master():
    """Idempotently enforce the six canonical V2 lifecycle stages."""
    desired = {row["stage_name"]: row for row in PIPELINE_STAGES}
    for stage in StageMaster.query.all():
        if stage.stage_name not in desired:
            # Development/demo data is disposable; production cleanup belongs in migration.
            db.session.delete(stage)
    db.session.flush()
    for stage_data in PIPELINE_STAGES:
        stage = StageMaster.query.filter_by(stage_name=stage_data["stage_name"]).first()
        if stage is None:
            stage = StageMaster(stage_name=stage_data["stage_name"])
            db.session.add(stage)
        stage.display_order = stage_data["display_order"]
        stage.requires_poc = stage_data["requires_poc"]
        stage.is_closed = False
        stage.is_won = False
    db.session.commit()
