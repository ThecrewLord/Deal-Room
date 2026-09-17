import { ROLES } from "../auth/roles";

const business = [
    "Dashboard",
    "Opportunities",
    "Accounts",
    "Stakeholders",
    "OEM Registry",
];

const pathMap = {
    Dashboard: "/dashboard",
    Opportunities: "/opportunities",
    Accounts: "/accounts",
    Stakeholders: "/stakeholders",
    "OEM Registry": "/oem-registry",
    POCs: "/pocs",
};

const pocRoles = [
    ROLES.SOLUTION_ENGINEER,
    ROLES.DELIVERY_MANAGER,
    ROLES.DEVOPS_ENGINEER,
    ROLES.DATA_ANALYST,
];

const businessNavigation = (role) => [
    ...business.map((name) => ({
        name,
        path: pathMap[name],
    })),
    ...(pocRoles.includes(role)
        ? [{ name: "POCs", path: pathMap.POCs }]
        : []),
];

const navigation = {
    [ROLES.LEADERSHIP]: [
        ...businessNavigation(ROLES.LEADERSHIP),
        { name: "Administration", path: "/admin/users" },
    ],

    [ROLES.ADMIN]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Administration", path: "/admin/users" },
    ],

    [ROLES.SALES_EXECUTIVE]: businessNavigation(ROLES.SALES_EXECUTIVE),

    [ROLES.SALES_MANAGER]: [
        ...businessNavigation(ROLES.SALES_MANAGER),
        { name: "Review Queue", path: "/sales-manager/review" },
        { name: "Team Performance", path: "/sales-manager/team-performance" },
    ],

    [ROLES.PRE_SALES_MANAGER]: [
        ...businessNavigation(ROLES.PRE_SALES_MANAGER),
        {
            name: "Pending Technical Assignment",
            path: "/pre-sales/assignments",
        },
        {
            name: "Team Performance",
            path: "/pre-sales/team-performance",
        },
    ],

    [ROLES.SOLUTION_ENGINEER]: businessNavigation(
        ROLES.SOLUTION_ENGINEER
    ),

    [ROLES.DELIVERY_MANAGER]: businessNavigation(
        ROLES.DELIVERY_MANAGER
    ),

    [ROLES.DEVOPS_ENGINEER]: businessNavigation(
        ROLES.DEVOPS_ENGINEER
    ),

    [ROLES.DATA_ANALYST]: businessNavigation(
        ROLES.DATA_ANALYST
    ),
};

export default navigation;
