// Canonical Deal Room v2 role vocabulary. The backend is authoritative.
export const ROLES = Object.freeze({
    LEADERSHIP: "Leadership",
    ADMIN: "Admin",
    SALES_MANAGER: "Sales Manager",
    SALES_EXECUTIVE: "Sales Executive",
    PRE_SALES_MANAGER: "Pre-Sales Manager",
    SOLUTION_ENGINEER: "Solution Engineer",
    DELIVERY_MANAGER: "Delivery Manager",
    DEVOPS_ENGINEER: "DevOps Engineer",
    DATA_ANALYST: "Data Analyst",
});

export const AVAILABLE_ROLES = Object.freeze([
    ROLES.LEADERSHIP,
    ROLES.ADMIN,
    ROLES.SALES_MANAGER,
    ROLES.SALES_EXECUTIVE,
    ROLES.PRE_SALES_MANAGER,
    ROLES.SOLUTION_ENGINEER,
    ROLES.DELIVERY_MANAGER,
    ROLES.DEVOPS_ENGINEER,
    ROLES.DATA_ANALYST,
]);

export const isValidRole = (role) => AVAILABLE_ROLES.includes(role);
