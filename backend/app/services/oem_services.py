from app.models.account.oem_partner import OEMPartner
from app.repositories.oem_repository import OEMRepository


class OEMService:

    @staticmethod
    def get_all():
        return OEMRepository.get_all()

    @staticmethod
    def get_by_id(oem_id):
        return OEMRepository.get_by_id(oem_id)

    @staticmethod
    def create(data):
        oem = OEMPartner(**data)
        return OEMRepository.create(oem)

    @staticmethod
    def update(oem_id, data):
        oem = OEMRepository.get_by_id(oem_id)

        if not oem:
            return None

        for key, value in data.items():
            setattr(oem, key, value)

        OEMRepository.update()
        return oem

    @staticmethod
    def delete(oem_id):
        oem = OEMRepository.get_by_id(oem_id)

        if not oem:
            return False

        OEMRepository.delete(oem)
        return True