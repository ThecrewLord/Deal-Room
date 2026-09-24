"""Canonical v2 role vocabulary.

`AVAILABLE_ROLES` is the only role vocabulary accepted by authorization and
role-management APIs.  The old ``Delivery`` label is retained only as a
Python import alias for legacy code/tests; it is deliberately not canonical
and can never be accepted from a JWT or API payload.
"""

LEADERSHIP = "Leadership"
ADMIN = "Admin"
SALES_MANAGER = "Sales Manager"
SALES_EXECUTIVE = "Sales Executive"
PRE_SALES_MANAGER = "Pre-Sales Manager"
SOLUTION_ENGINEER = "Solution Engineer"
DELIVERY_MANAGER = "Delivery Manager"
DEVOPS_ENGINEER = "DevOps Engineer"
DATA_ANALYST = "Data Analyst"

# Legacy compatibility only.  Do not add this to AVAILABLE_ROLES and never
# normalize it during authentication; legacy database data must be migrated.
LEGACY_DELIVERY = "Delivery"
DELIVERY = SOLUTION_ENGINEER

AVAILABLE_ROLES = [
    LEADERSHIP,
    ADMIN,
    SALES_MANAGER,
    SALES_EXECUTIVE,
    PRE_SALES_MANAGER,
    SOLUTION_ENGINEER,
    DELIVERY_MANAGER,
    DEVOPS_ENGINEER,
    DATA_ANALYST,
]

DEFAULT_ROLE = SALES_EXECUTIVE


def normalize_role(role):
    """Return a role unchanged.

    Authentication must never turn a retired role name into a privileged
    canonical role.  This function remains for compatibility with callers;
    migrations/seeders are responsible for legacy-data conversion.
    """
    return role


def is_valid_role(role):
    return role in AVAILABLE_ROLES
