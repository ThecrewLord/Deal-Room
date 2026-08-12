import {
    useEffect,
    useState,
} from "react";

import {
    getDashboardSummary,
} from "../../api/dashboardApi";

import { useAuth } from "../../context/AuthContext";

import FigmaDashboard from "./FigmaDashboard";

const Dashboard = () => {
    const {
        user,
        loading: authLoading,
    } = useAuth();

    const [
        dashboard,
        setDashboard,
    ] = useState(null);

    const [
        loading,
        setLoading,
    ] = useState(true);

    const [
        error,
        setError,
    ] = useState("");

    useEffect(() => {
        let mounted = true;

        const loadDashboard = async () => {
            try {
                setLoading(true);

                const response =
                    await getDashboardSummary();

                if (!mounted) {
                    return;
                }

                setDashboard(response);

                setError("");
            } catch (err) {
                if (!mounted) {
                    return;
                }

                setError(
                    err?.response?.data
                        ?.message ||
                    "Unable to load dashboard."
                );
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
            <DashboardLoading />
        );
    }

    if (error) {
        return (
            <DashboardError
                message={error}
            />
        );
    }

    return (
        <FigmaDashboard
            dashboard={dashboard}
            user={user}
        />
    );
};

function DashboardLoading() {
    return (
        <div className="figma-dashboard-loading">
            <div className="dashboard-loading-title" />

            <div className="dashboard-loading-grid">
                {Array.from({
                    length: 8,
                }).map((_, index) => (
                    <div
                        key={index}
                        className="dashboard-loading-card"
                    />
                ))}
            </div>

            <div className="dashboard-loading-large" />
        </div>
    );
}

function DashboardError({
    message,
}) {
    return (
        <div className="figma-dashboard-error">
            <div>
                <h2>
                    Unable to load dashboard
                </h2>

                <p>
                    {message}
                </p>

                <button
                    onClick={() =>
                        window.location.reload()
                    }
                >
                    Retry
                </button>
            </div>
        </div>
    );
}

export default Dashboard;