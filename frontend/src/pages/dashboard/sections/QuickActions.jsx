import { useNavigate } from "react-router-dom";
import { ROLES } from "../../../auth/roles";
import { useAuth } from "../../../context/AuthContext";

const ACTIONS = {
    [ROLES.SALES_EXECUTIVE]: [
        ["New Opportunity", "Create a new sales lead", "/opportunities"],
        ["Opportunities", "Manage sales opportunities", "/opportunities"],
        ["Accounts", "View authorized accounts", "/accounts"],
    ],
    [ROLES.SALES_MANAGER]: [
        ["Review Queue", "Review submitted opportunities", "/sales-manager/review"],
        ["Opportunities", "View authorized opportunities", "/opportunities"],
        ["Accounts", "View authorized accounts", "/accounts"],
    ],
    [ROLES.PRE_SALES_MANAGER]: [
        ["Technical Assignment", "Assign technical teams", "/pre-sales/assignments"],
        ["Opportunities", "View authorized opportunities", "/opportunities"],
    ],
    [ROLES.SOLUTION_ENGINEER]: [
        ["Opportunities", "Work assigned opportunities", "/opportunities"],
        ["POCs", "Review assigned POCs", "/pocs"],
        ["Stakeholders", "Manage technical stakeholders", "/stakeholders"],
    ],
};

export default function QuickActions() {
    const navigate = useNavigate();
    const { activeRole } = useAuth();
    const actions = ACTIONS[activeRole] || [];

    return (
        <div className="dashboard-panel">
            <div className="panel-header"><h2>Quick Actions</h2></div>
            <div className="quick-actions">
                {actions.map(([title, subtitle, route]) => (
                    <button key={title} className="action-btn" onClick={() => navigate(route)}>
                        <strong>{title}</strong>
                        <small>{subtitle}</small>
                    </button>
                ))}
            </div>
        </div>
    );
}
