from app.constants.stages import PIPELINE_STAGES
from app.database import db
from app.models.opportunity.stage_master import StageMaster


def seed_stage_master():
    for stage_data in PIPELINE_STAGES:
        stage = StageMaster.query.filter_by(
            stage_name=stage_data["stage_name"]
        ).first()

        if stage is None:
            stage = StageMaster(stage_name=stage_data["stage_name"])
            db.session.add(stage)

        stage.display_order = stage_data["display_order"]
        stage.requires_poc = stage_data["requires_poc"]
        stage.is_closed = stage_data["is_closed"]
        stage.is_won = stage_data["is_won"]

    db.session.commit()
