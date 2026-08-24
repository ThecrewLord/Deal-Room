"""Canonical organization and manager policy for Admin management."""

from app.constants.roles import (
    ADMIN,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
)

ADMINISTRATION = "ADMINISTRATION"
SALES = "SALES"
PRE_SALES_TECHNICAL = "PRE_SALES_TECHNICAL"

ROLE_ORGANIZATIONS = {
    ADMIN: ADMINISTRATION,
    SALES_EXECUTIVE: SALES,
    SALES_MANAGER: SALES,
    PRE_SALES_MANAGER: PRE_SALES_TECHNICAL,
    SOLUTION_ENGINEER: PRE_SALES_TECHNICAL,
}

ROLE_MANAGER_REQUIREMENTS = {
    SALES_EXECUTIVE: {SALES_MANAGER},
    SOLUTION_ENGINEER: {PRE_SALES_MANAGER},
    SALES_MANAGER: set(),
    PRE_SALES_MANAGER: set(),
    ADMIN: set(),
}


def get_organizations_for_roles(roles):
    """Return distinct organizations derived only from current roles."""
    return sorted({ROLE_ORGANIZATIONS[role] for role in roles if role in ROLE_ORGANIZATIONS})


def get_organization_for_roles(roles):
    """Return a stable display value for a user's current role set."""
    organizations = get_organizations_for_roles(roles)
    order = {ADMINISTRATION: 0, SALES: 1, PRE_SALES_TECHNICAL: 2}
    organizations.sort(key=lambda value: order.get(value, 99))
    return " + ".join(organizations) if organizations else None


def get_required_manager_roles(roles):
    """Return manager roles a candidate must satisfy for every assigned role."""
    required = set()
    for role in roles:
        required.update(ROLE_MANAGER_REQUIREMENTS.get(role, set()))
    return required
