"""Authoritative Deal Room v2 lifecycle/state vocabulary."""

LIFECYCLE_STAGES = (
    "Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery",
)
OUTCOMES = ("Open", "Closed Won", "Closed Lost")
OPERATIONAL_STATUSES = ("Active", "Stalled", "Closed")
REVIEW_STATUSES = ("Draft", "Pending Sales Manager Review", "Approved")

PIPELINE_STAGES = [
    {"display_order": 1, "stage_name": "Lead", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 2, "stage_name": "Qualified", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 3, "stage_name": "RFX", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 4, "stage_name": "POC", "requires_poc": True, "is_closed": False, "is_won": False},
    {"display_order": 5, "stage_name": "Negotiations", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 6, "stage_name": "Delivery", "requires_poc": False, "is_closed": False, "is_won": False},
]

INITIAL_STAGE_NAME = "Lead"
QUALIFICATION_STAGE_NAME = "Qualified"
OPEN_STATUS = "Open"
PENDING_SALES_MANAGER_REVIEW_STATUS = "Pending Sales Manager Review"
APPROVED_STATUS = "Approved"
ACTIVE_STATUS = "Active"
CLOSED_STATUS = "Closed"
