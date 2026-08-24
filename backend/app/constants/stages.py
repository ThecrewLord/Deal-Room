PIPELINE_STAGES = [
    {"display_order": 1, "stage_name": "Lead / Identified", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 2, "stage_name": "Qualification", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 3, "stage_name": "Discovery", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 4, "stage_name": "POC / Technical Evaluation", "requires_poc": True, "is_closed": False, "is_won": False},
    {"display_order": 5, "stage_name": "Proposal", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 6, "stage_name": "Negotiation", "requires_poc": False, "is_closed": False, "is_won": False},
    {"display_order": 7, "stage_name": "Closed Won", "requires_poc": False, "is_closed": True, "is_won": True},
    {"display_order": 8, "stage_name": "Closed Lost", "requires_poc": False, "is_closed": True, "is_won": False},
]

INITIAL_STAGE_NAME = "Lead / Identified"
QUALIFICATION_STAGE_NAME = "Qualification"
OPEN_STATUS = "Open"
PENDING_SALES_MANAGER_REVIEW_STATUS = "Pending Sales Manager Review"
APPROVED_STATUS = "Approved"
ACTIVE_STATUS = "Active"
REJECTED_STATUS = "Rejected"
CLOSED_STATUS = "Closed"
