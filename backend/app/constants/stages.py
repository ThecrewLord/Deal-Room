"""Opportunity lifecycle vocabulary for Deal Room v2.

Legacy stage names remain available for read/seed compatibility.  They are
not v2 lifecycle states and must never be used as authorization decisions.
"""

LIFECYCLE_STAGES = (
    "Lead",
    "Qualified",
    "RFX",
    "POC",
    "Negotiations",
    "Delivery",
)

OUTCOMES = ("Open", "Closed Won", "Closed Lost")
OPERATIONAL_STATUSES = ("Active", "Stalled", "Closed")
REVIEW_STATUSES = ("Draft", "Pending Sales Manager Review", "Approved", "Rejected")

# Explicit, lossless read/compatibility mapping. Historical StageMaster rows
# are never renamed or deleted by A2.
LEGACY_STAGE_TO_LIFECYCLE = {
    "Lead / Identified": "Lead",
    "Qualification": "Qualified",
    "Discovery": "RFX",
    "POC / Technical Evaluation": "POC",
    "Proposal": "Negotiations",
    "Negotiation": "Negotiations",
}
LIFECYCLE_TO_LEGACY_STAGE = {
    "Lead": "Lead / Identified",
    "Qualified": "Qualification",
    "RFX": "Discovery",
    "POC": "POC / Technical Evaluation",
    "Negotiations": "Negotiation",
}

# Legacy constants retained for compatibility with existing reports/services.
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
