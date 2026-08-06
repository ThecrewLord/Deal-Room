import { useEffect, useState } from "react";

import { getDashboardSummary } from "../../api/dashboardApi";
import { useAuth } from "../../context/AuthContext";

import SalesExecutiveDashboard from "./roles/SalesExecutiveDashboard";
import PresalesDashboard from "./roles/PresalesDashboard";
import ManagerDashboard from "./roles/ManagerDashboard";

const Dashboard = () => {
    const {
        user,
        activeRole,
        loading: authLoading,
    } = useAuth();

    const [dashboard, setDashboard] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let mounted = true;

        const loadDashboard = async () => {
            try {
                const response =
                    await getDashboardSummary();

                if (mounted) {
                    setDashboard(response);
                    setError("");
                }
            } catch (err) {
                if (mounted) {
                    setError(
                        err?.response?.data
                            ?.message ??
                            "Unable to load dashboard."
                    );
                }
            } finally {
                if (mounted) {
                    setLoading(false);
                }
            }
        };

        if (!authLoading) {
            loadDashboard();
        }

        return () => {
            mounted = false;
        };
    }, [authLoading]);

    if (authLoading || loading) {
        return (
            <div className="dashboard-loading">
                Loading dashboard...
            </div>
        );
    }

    if (error) {
        return (
            <div className="dashboard-error">
                {error}
            </div>
        );
    }

    switch (activeRole) {
        case "Sales Executive":
            return (
                <SalesExecutiveDashboard
                    user={user}
                    dashboard={dashboard}
                />
            );

        case "Pre-Sales Consultant":
            return (
                <PresalesDashboard
                    user={user}
                    dashboard={dashboard}
                />
            );

        case "Sales Manager":
            return (
                <ManagerDashboard
                    user={user}
                    dashboard={dashboard}
                />
            );

        default:
            return (
                <div className="dashboard-error">
                    No dashboard is available for your assigned role.
                </div>
            );
    }
};

export default Dashboard;