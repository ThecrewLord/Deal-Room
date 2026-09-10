# Canonical business roles for the Deal Room application.

ADMIN = "Admin"
SALES_EXECUTIVE = "Sales Executive"
SALES_MANAGER = "Sales Manager"
PRE_SALES_MANAGER = "Pre-Sales Manager"
SOLUTION_ENGINEER = "Solution Engineer"

# Existing/general Delivery role.
# Kept for backward compatibility with Phase 5 and older data.
DELIVERY = "Delivery"
LEGACY_DELIVERY = DELIVERY

# Additional operational roles introduced for the delivery workflow.
DELIVERY_MANAGER = "Delivery Manager"
DEVOPS_ENGINEER = "DevOps Engineer"
DATA_ANALYST = "Data Analyst"

# Original six canonical roles expected by the Phase 1 contract.
AVAILABLE_ROLES = [
    ADMIN,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
    DELIVERY,
]

# Roles added by later delivery functionality.
OPERATIONAL_ROLES = [
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
]

# All roles that the application currently recognizes.
SUPPORTED_ROLES = AVAILABLE_ROLES + OPERATIONAL_ROLES

DEFAULT_ROLE = SALES_EXECUTIVE


def normalize_role(role):
    """
    Return the canonical role name.
    """
    return role


def is_valid_role(role):
    """Return True when *role* is a supported business role."""
    return normalize_role(role) in SUPPORTED_ROLES
