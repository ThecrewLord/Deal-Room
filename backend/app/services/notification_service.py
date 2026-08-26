from app.constants.roles import (
    ADMIN,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
)
from app.database import db
from app.models.system.notification import Notification
from app.models.opportunity.opportunity import Opportunity
from app.models.opportunity.poc_tracker import POCTracker
from app.models.account.account import Account
from app.models.opportunity.stakeholder import Stakeholder
from app.auth.authorization import AuthorizationService
from app.repositories.notification_repository import NotificationRepository


ROLE_BY_NOTIFICATION = {
    "OPPORTUNITY_SUBMITTED_FOR_REVIEW": SALES_MANAGER,
    "OPPORTUNITY_APPROVED": PRE_SALES_MANAGER,
    "OPPORTUNITY_REJECTED": SALES_EXECUTIVE,
    "SALES_OWNER_ASSIGNED": SALES_EXECUTIVE,
    "OPPORTUNITY_SENT_TO_PRE_SALES": PRE_SALES_MANAGER,
    "SOLUTION_ENGINEER_ASSIGNED": SOLUTION_ENGINEER,
    "POC_REQUESTED": PRE_SALES_MANAGER,
    "POC_APPROVED": SOLUTION_ENGINEER,
    "POC_REJECTED": SOLUTION_ENGINEER,
    "POC_RESULT_SUBMITTED": SOLUTION_ENGINEER,
}

BUSINESS_ENTITY_TYPES = {"opportunity", "poc", "account", "stakeholder"}
ADMIN_ENTITY_TYPES = {"admin", "user", "access"}


class NotificationService:
    @staticmethod
    def queue(user_id, notification_type, entity_type, entity_id, message):
        # A notification is created only at an explicit workflow transition.
        # Keep it in the caller's transaction so business mutation, audit and
        # notification either commit together or roll back together.
        return NotificationRepository.create(Notification(
            recipient_user_id=user_id,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            is_read=False,
        ))

    @staticmethod
    def _entity_authorized(notification, user, active_role):
        entity_type = (notification.entity_type or "").lower()
        if active_role == ADMIN:
            return entity_type in ADMIN_ENTITY_TYPES
        if entity_type not in BUSINESS_ENTITY_TYPES:
            return False
        if notification.entity_id is None:
            return False
        if entity_type == "opportunity":
            entity = Opportunity.query.get(notification.entity_id)
            return AuthorizationService.can_view_opportunity(user, active_role, entity)
        if entity_type == "poc":
            entity = POCTracker.query.get(notification.entity_id)
            return AuthorizationService.can_view_poc(user, active_role, entity)
        if entity_type == "account":
            entity = Account.query.get(notification.entity_id)
            return AuthorizationService.can_view_account(user, active_role, entity)
        if entity_type == "stakeholder":
            entity = Stakeholder.query.get(notification.entity_id)
            return AuthorizationService.can_view_stakeholder(user, active_role, entity)
        return False

    @staticmethod
    def _visible(notification, user, active_role):
        expected_role = ROLE_BY_NOTIFICATION.get(notification.notification_type)
        if active_role == ADMIN:
            return notification.entity_type.lower() in ADMIN_ENTITY_TYPES and expected_role is None
        # Unknown notification types are not exposed to a business role.
        if expected_role != active_role:
            return False
        return NotificationService._entity_authorized(notification, user, active_role)

    @staticmethod
    def get_for_user(user, active_role, unread_only=False):
        notifications = NotificationRepository.get_for_user(user.user_id, unread_only)
        return [n for n in notifications if NotificationService._visible(n, user, active_role)]

    @staticmethod
    def mark_read(notification_id, user, active_role):
        notification = Notification.query.filter_by(
            notification_id=notification_id,
            recipient_user_id=user.user_id,
        ).first()
        if not notification or not NotificationService._visible(notification, user, active_role):
            return None
        notification.is_read = True
        db.session.commit()
        return notification
