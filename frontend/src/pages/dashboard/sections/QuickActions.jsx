import { useNavigate } from "react-router-dom";

const QuickActions = () => {
    const navigate = useNavigate();

    return (
        <div className="dashboard-panel">
            <div className="panel-header">
                <h2>Quick Actions</h2>
            </div>

            <div className="quick-actions">

                <button
                    className="action-btn"
                    onClick={() => navigate("/opportunities")}
                >
                    Opportunities
                </button>

                <button
                    className="action-btn"
                    onClick={() => navigate("/accounts")}
                >
                    Accounts
                </button>

                <button
                    className="action-btn"
                    onClick={() => navigate("/activities")}
                >
                    Activities
                </button>

                <button
                    className="action-btn"
                    onClick={() => navigate("/poc")}
                >
                    POCs
                </button>

            </div>
        </div>
    );
};

export default QuickActions;