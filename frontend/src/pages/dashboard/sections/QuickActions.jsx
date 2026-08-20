import { useNavigate } from "react-router-dom";

const QuickActions = () => {
    const navigate = useNavigate();

    const actions = [
        {
            title: "Opportunities",
            subtitle: "Manage sales opportunities",
            route: "/opportunities",
        },
        {
            title: "Accounts",
            subtitle: "View customer accounts",
            route: "/accounts",
        },
        {
            title: "Activities",
            subtitle: "Track daily activities",
            route: "/activities",
        },
        {
            title: "POCs",
            subtitle: "Proof of Concepts",
            route: "/poc",
        },
    ];

    return (
        <div className="dashboard-panel">
            <div className="panel-header">
                <h2>Quick Actions</h2>
            </div>

            <div className="quick-actions">
                {actions.map((action) => (
                    <button
                        key={action.route}
                        className="action-btn"
                        onClick={() => navigate(action.route)}
                    >
                        <strong>{action.title}</strong>

                        <small>{action.subtitle}</small>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default QuickActions;