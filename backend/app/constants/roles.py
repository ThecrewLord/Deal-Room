# Canonical business roles for the Deal Room application.
#
# Solution Engineer is the single technical individual-contributor role.
# The former Delivery role is intentionally no longer a distinct business role.

ADMIN = "Admin"
SALES_EXECUTIVE = "Sales Executive"
SALES_MANAGER = "Sales Manager"
PRE_SALES_MANAGER = "Pre-Sales Manager"
SOLUTION_ENGINEER = "Solution Engineer"

# Backward-compatible constant for older imports. It resolves to the unified
# Solution Engineer role so legacy code cannot create a separate Delivery role.
DELIVERY = SOLUTION_ENGINEER
LEGACY_DELIVERY = "Delivery"

AVAILABLE_ROLES = [
    ADMIN,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
]

DEFAULT_ROLE = SALES_EXECUTIVE


def normalize_role(role):
    """Map the retired Delivery role to the unified Solution Engineer role."""
    return SOLUTION_ENGINEER if role == LEGACY_DELIVERY else role


def is_valid_role(role):
    """Return True when *role* is one of the current canonical roles."""
    return normalize_role(role) in AVAILABLE_ROLES
