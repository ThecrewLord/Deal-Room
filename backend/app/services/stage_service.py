from app.repositories.stage_repository import StageRepository


class StageService:

    @staticmethod
    def get_all():
        return StageRepository.get_all()

    @staticmethod
    def get_by_id(stage_id):
        return StageRepository.get_by_id(stage_id)
