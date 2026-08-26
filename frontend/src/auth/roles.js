// Canonical role vocabulary shared by authentication, navigation and role UI.
export const ROLES = Object.freeze({
    ADMIN: "Admin",
    SALES_EXECUTIVE: "Sales Executive",
    SALES_MANAGER: "Sales Manager",
    PRE_SALES_MANAGER: "Pre-Sales Manager",
    SOLUTION_ENGINEER: "Solution Engineer",
});

export const AVAILABLE_ROLES = Object.freeze([
    ROLES.ADMIN,
    ROLES.SALES_EXECUTIVE,
    ROLES.SALES_MANAGER,
    ROLES.PRE_SALES_MANAGER,
    ROLES.SOLUTION_ENGINEER,
]);

export const isValidRole = (role) =>
    AVAILABLE_ROLES.includes(role);
