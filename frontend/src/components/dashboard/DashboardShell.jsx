import { RefreshCw } from "lucide-react";
import PageHeader from "../ui/PageHeader";
import Button from "../ui/Button";

const firstName = (name) => name?.trim()?.split(/\s+/)[0] || "there";

export default function DashboardShell({ user, role, description, onRefresh, refreshing = false, children }) {
    return (
        <div className="deal-dashboard fade-in">
            <PageHeader
                title={`Good morning, ${firstName(user?.full_name)} 👋`}
                description={description}
                actions={onRefresh ? <Button variant="secondary" onClick={onRefresh} disabled={refreshing}><RefreshCw size={14} className={refreshing ? "ui-spin" : ""} /> Refresh</Button> : null}
            />
            <div className="dashboard-context-row">
                <span>Sales Intelligence</span>
                <strong>{role}</strong>
            </div>
            {children}
        </div>
    );
}
