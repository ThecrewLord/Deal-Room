"""Canonical v2 organizations and manager eligibility rules."""

from app.constants.roles import (
    ADMIN,
    DATA_ANALYST,
    DEVOPS_ENGINEER,
    DELIVERY_MANAGER,
    LEADERSHIP,
    PRE_SALES_MANAGER,
    SALES_EXECUTIVE,
    SALES_MANAGER,
    SOLUTION_ENGINEER,
)

GOVERNANCE = "GOVERNANCE"
ADMINISTRATION = "ADMINISTRATION"
SALES = "SALES"
PRE_SALES_TECHNICAL = "PRE_SALES_TECHNICAL"
DELIVERY_TECHNICAL = "DELIVERY_TECHNICAL"

ROLE_ORGANIZATIONS = {
    LEADERSHIP: GOVERNANCE,
    ADMIN: ADMINISTRATION,
    SALES_MANAGER: SALES,
    SALES_EXECUTIVE: SALES,
    PRE_SALES_MANAGER: PRE_SALES_TECHNICAL,
    SOLUTION_ENGINEER: PRE_SALES_TECHNICAL,
    DELIVERY_MANAGER: DELIVERY_TECHNICAL,
    DEVOPS_ENGINEER: DELIVERY_TECHNICAL,
    DATA_ANALYST: DELIVERY_TECHNICAL,
}

ROLE_MANAGER_REQUIREMENTS = {
    LEADERSHIP: set(),
    ADMIN: set(),
    SALES_MANAGER: set(),
    SALES_EXECUTIVE: {SALES_MANAGER},
    PRE_SALES_MANAGER: set(),
    SOLUTION_ENGINEER: {PRE_SALES_MANAGER},
    DELIVERY_MANAGER: set(),
    DEVOPS_ENGINEER: {DELIVERY_MANAGER},
    DATA_ANALYST: {DELIVERY_MANAGER},
}


def get_organizations_for_roles(roles):
    return sorted({ROLE_ORGANIZATIONS[role] for role in roles if role in ROLE_ORGANIZATIONS})


def get_organization_for_roles(roles):
    organizations = get_organizations_for_roles(roles)
    order = {
        GOVERNANCE: 0,
        ADMINISTRATION: 1,
        SALES: 2,
        PRE_SALES_TECHNICAL: 3,
        DELIVERY_TECHNICAL: 4,
    }
    organizations.sort(key=lambda value: order.get(value, 99))
    return " + ".join(organizations) if organizations else None


def get_required_manager_roles(roles):
    required = set()
    for role in roles:
        required.update(ROLE_MANAGER_REQUIREMENTS.get(role, set()))
    return required
