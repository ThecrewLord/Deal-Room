import { ROLES } from "../auth/roles";

const navigation = {
    [ROLES.LEADERSHIP]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Administration", path: "/admin/users" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
    ],

    [ROLES.ADMIN]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Administration", path: "/admin/users" },
    ],

    [ROLES.SALES_EXECUTIVE]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
    ],

    [ROLES.SALES_MANAGER]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Review Queue", path: "/sales-manager/review" },
        { name: "Team Performance", path: "/sales-manager/team-performance" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
    ],

    [ROLES.PRE_SALES_MANAGER]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Pending Technical Assignment", path: "/pre-sales/assignments" },
        { name: "Team Performance", path: "/pre-sales/team-performance" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
    ],

    [ROLES.SOLUTION_ENGINEER]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
        { name: "POCs", path: "/pocs" },
        { name: "Stakeholders", path: "/stakeholders" },
        { name: "OEM Registry", path: "/oem-registry" },
    ],

    [ROLES.DELIVERY_MANAGER]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
    ],

    [ROLES.DEVOPS_ENGINEER]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
    ],

    [ROLES.DATA_ANALYST]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "Accounts", path: "/accounts" },
    ],
};

export default navigation;
