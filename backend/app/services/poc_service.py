from app.repositories.poc_repository import PocRepository


class PocService:

    @staticmethod
    def create_poc(data):
        return PocRepository.create(data)

    @staticmethod
    def get_by_id(poc_id):
        return PocRepository.get_by_id(poc_id)

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return PocRepository.get_by_opportunity(opportunity_id)

    @staticmethod
    def update_poc(poc_id, data):
        poc = PocRepository.get_by_id(poc_id)

        if not poc:
            return None

        incoming_updated_at = data.pop("updated_at", None)

        if incoming_updated_at and poc.updated_at:
            if incoming_updated_at.replace(tzinfo=None) != poc.updated_at.replace(tzinfo=None):
                raise RuntimeError(
                    "This POC was updated by someone else. Please reload and try again."
                )

        return PocRepository.update(poc, data)

    @staticmethod
    def delete_poc(poc_id):
        poc = PocRepository.get_by_id(poc_id)

        if not poc:
            return False

        return PocRepository.delete(poc)