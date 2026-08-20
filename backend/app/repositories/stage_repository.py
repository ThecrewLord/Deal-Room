from app.models.opportunity.stage_master import StageMaster


class StageRepository:

    @staticmethod
    def get_all():
        return StageMaster.query.order_by(StageMaster.display_order).all()

    @staticmethod
    def get_by_id(stage_id):
        return StageMaster.query.get(stage_id)
