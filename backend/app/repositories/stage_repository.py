from app.database import db
from app.models.opportunity.stage_master import StageMaster
from app.models.opportunity.stage_history import StageHistory


class StageRepository:

    @staticmethod
    def get_by_id(stage_id):
        return StageMaster.query.filter_by(stage_id=stage_id).first()

    @staticmethod
    def get_by_name(stage_name):
        return StageMaster.query.filter_by(stage_name=stage_name).first()

    @staticmethod
    def get_all():
        return StageMaster.query.order_by(StageMaster.display_order.asc()).all()

    @staticmethod
    def add_history(opportunity_id, stage_id, changed_by=None, remarks=None):
        history = StageHistory(
            opportunity_id=opportunity_id,
            stage_id=stage_id,
            changed_by=changed_by,
            remarks=remarks,
        )
        db.session.add(history)
        return history

    @staticmethod
    def get_history(opportunity_id):
        return StageHistory.query.filter_by(
            opportunity_id=opportunity_id
        ).order_by(StageHistory.created_at.asc()).all()
