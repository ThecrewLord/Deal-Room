from app.auth.authorization import (
    AuthorizationDenied,
    AuthorizationService,
)
from app.database import db
from app.repositories.oem_repository import OEMRepository


class OEMService:

    @staticmethod
    def get_all(user, active_role):
        return OEMRepository.get_by_accounts(
            AuthorizationService.account_query(
                user,
                active_role,
            )
        )

    @staticmethod
    def get_by_id(oem_id, user, active_role):
        oem = OEMRepository.get_by_id(oem_id)

        if not AuthorizationService.can_view_oem(
            user,
            active_role,
            oem,
        ):
            return None

        return oem

    @staticmethod
    def create(data, user, active_role):
        if not AuthorizationService.can_manage_oem(
            user,
            active_role,
        ):
            raise AuthorizationDenied(
                "You are not authorized to create OEM partners."
            )

        required_fields = (
            "account_id",
            "partner_name",
            "product_name",
        )

        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"{field} is required.")

        partner_name = str(data["partner_name"]).strip()

        if not partner_name:
            raise ValueError("partner_name is required.")

        account = OEMRepository.get_account(
            data["account_id"]
        )

        if not account:
            raise ValueError("Account not found.")

        existing = OEMRepository.get_by_partner_name(
            partner_name
        )

        if existing:
            raise ValueError(
                "An OEM partner with this name already exists."
            )

        allowed_fields = {
            "account_id",
            "partner_name",
            "product_name",
            "contact_person",
            "email",
            "phone",
            "status",
            "notes",
        }

        cleaned_data = {
            key: value
            for key, value in data.items()
            if key in allowed_fields
        }

        cleaned_data["partner_name"] = partner_name

        return OEMRepository.create_from_data(
            cleaned_data
        )

    @staticmethod
    def update(oem_id, data, user, active_role):
        oem = OEMRepository.get_by_id(oem_id)

        if not oem:
            return None

        if not AuthorizationService.can_manage_oem(
            user,
            active_role,
            oem,
        ):
            raise AuthorizationDenied(
                "You are not authorized to update this OEM partner."
            )

        if "partner_name" in data:
            partner_name = str(data["partner_name"]).strip()

            if not partner_name:
                raise ValueError(
                    "partner_name cannot be empty."
                )

            existing = OEMRepository.get_by_partner_name(
                partner_name
            )

            if (
                existing
                and existing.oem_partner_id
                != oem.oem_partner_id
            ):
                raise ValueError(
                    "An OEM partner with this name already exists."
                )

            oem.partner_name = partner_name

        allowed_fields = {
            "product_name",
            "contact_person",
            "email",
            "phone",
            "status",
            "notes",
        }

        for field in allowed_fields:
            if field in data:
                setattr(oem, field, data[field])

        db.session.commit()

        return oem

    @staticmethod
    def delete(oem_id, user, active_role):
        oem = OEMRepository.get_by_id(oem_id)

        if not oem:
            return False

        if not AuthorizationService.can_manage_oem(
            user,
            active_role,
            oem,
        ):
            raise AuthorizationDenied(
                "You are not authorized to delete this OEM partner."
            )

        db.session.delete(oem)
        db.session.commit()

        return True
