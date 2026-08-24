from app.auth.authorization import AuthorizationDenied, AuthorizationService
from app.repositories.oem_repository import OEMRepository


class OEMService:
    @staticmethod
    def get_all(user, active_role):
        return OEMRepository.get_by_accounts(AuthorizationService.account_query(user, active_role))

    @staticmethod
    def get_by_id(oem_id, user, active_role):
        oem = OEMRepository.get_by_id(oem_id)
        if not AuthorizationService.can_view_oem(user, active_role, oem):
            return None
        return oem

    @staticmethod
    def create(data, user, active_role):
        raise AuthorizationDenied("OEM Partner creation is not permitted in Phase 2.")

    @staticmethod
    def update(oem_id, data, user, active_role):
        oem = OEMService.get_by_id(oem_id, user, active_role)
        if not oem:
            return None
        # Phase 2 establishes visibility; OEM mutation remains deferred.
        raise AuthorizationDenied("OEM Partner mutation is not permitted in Phase 2.")

    @staticmethod
    def delete(oem_id, user, active_role):
        oem = OEMService.get_by_id(oem_id, user, active_role)
        if not oem:
            return False
        raise AuthorizationDenied("OEM Partner deletion is not permitted in Phase 2.")
