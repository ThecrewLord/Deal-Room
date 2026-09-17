import { RefreshCw } from "lucide-react";
import PageHeader from "../ui/PageHeader";
import Button from "../ui/Button";

const firstName = (name) => name?.trim()?.split(/\s+/)[0] || "there";

const getGreeting = () => {
    const hour = new Date().getHours();

    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
};

const getContextLabel = (role) => {
    if (role === "Admin") return "Platform Administration";
    if (
        role === "Delivery Manager" ||
        role === "DevOps Engineer" ||
        role === "Data Analyst"
    ) {
        return "Delivery & Technical Operations";
    }
    if (
        role === "Solution Engineer" ||
        role === "Pre-Sales Manager"
    ) {
        return "Technical Intelligence";
    }
    return "Sales Intelligence";
};

export default function DashboardShell({
    user,
    role,
    description,
    onRefresh,
    refreshing = false,
    children,
}) {
    return (
        <div className="deal-dashboard fade-in">
            <PageHeader
                title={`${getGreeting()}, ${firstName(user?.full_name)} 👋`}
                description={description}
                actions={
                    onRefresh ? (
                        <Button
                            variant="secondary"
                            onClick={onRefresh}
                            disabled={refreshing}
                        >
                            <RefreshCw
                                size={14}
                                className={refreshing ? "ui-spin" : ""}
                            />
                            Refresh
                        </Button>
                    ) : null
                }
            />

            <div className="dashboard-context-row">
                <span>{getContextLabel(role)}</span>
                <strong>{role}</strong>
            </div>

            {children}
        </div>
    );
}
