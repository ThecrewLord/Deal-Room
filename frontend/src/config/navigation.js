import { ROLES } from "../auth/roles";

const navigation = {
    [ROLES.ADMIN]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Pending Approvals", path: "/admin/approval" },
        { name: "Users", path: "/admin/users" },
        { name: "Role Management", path: "/admin/roles" },
        { name: "Access Management", path: "/admin/access" },
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
    ],

    [ROLES.SOLUTION_ENGINEER]: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Opportunities", path: "/opportunities" },
        { name: "POCs", path: "/pocs" },
        { name: "Stakeholders", path: "/stakeholders" },
        { name: "OEM Registry", path: "/oem-registry" },
    ],

};

export default navigation;
