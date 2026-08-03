from app.repositories.stakeholder_repository import StakeholderRepository


class StakeholderService:

    @staticmethod
    def create_stakeholder(data):
        return StakeholderRepository.create(data)

    @staticmethod
    def get_by_id(stakeholder_id):
        return StakeholderRepository.get_by_id(stakeholder_id)

    @staticmethod
    def get_by_opportunity(opportunity_id):
        return StakeholderRepository.get_by_opportunity(opportunity_id)

    @staticmethod
    def update_stakeholder(stakeholder_id, data):
        stakeholder = StakeholderRepository.get_by_id(stakeholder_id)

        if not stakeholder:
            return None

        incoming_updated_at = data.pop("updated_at", None)

        if incoming_updated_at and stakeholder.updated_at:
            if incoming_updated_at.replace(tzinfo=None) != stakeholder.updated_at.replace(tzinfo=None):
                raise RuntimeError(
                    "This stakeholder was updated by someone else. Please reload and try again."
                )

        return StakeholderRepository.update(stakeholder, data)

    @staticmethod
    def delete_stakeholder(stakeholder_id):
        stakeholder = StakeholderRepository.get_by_id(stakeholder_id)

        if not stakeholder:
            return False

        return StakeholderRepository.delete(stakeholder)