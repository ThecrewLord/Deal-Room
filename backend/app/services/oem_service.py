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

        existing = OEMRepository.get_by_partner_name(
            data["partner_name"]
        )

        if existing:
            raise ValueError(
                "OEM Partner already exists."
            )

        oem = OEMPartner(**data)

        return OEMRepository.create(oem)

    @staticmethod
    def update(oem_id, data):

        oem = OEMRepository.get_by_id(oem_id)

        if not oem:
            return None

        existing = OEMRepository.get_by_partner_name(
            data.get("partner_name")
        )

        if (
            existing
            and existing.oem_partner_id != oem.oem_partner_id
        ):
            raise ValueError(
                "OEM Partner already exists."
            )

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