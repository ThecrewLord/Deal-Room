import { Activity, CheckCircle2, Circle, TrendingUp, XCircle } from "lucide-react";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";

const iconFor = (action) => {
    const value = String(action || "").toUpperCase();
    if (value.includes("CREATE")) return CheckCircle2;
    if (value.includes("DELETE")) return XCircle;
    if (value.includes("UPDATE")) return TrendingUp;
    return Circle;
};

const formatDate = (value) => {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
};

export default function RecentActivity({ activity = [] }) {
    return (
        <Card className="dashboard-list-card">
            <div className="dashboard-card-header">
                <div>
                    <h2>Recent Activity</h2>
                    <p>Latest authorized opportunity updates.</p>
                </div>
            </div>
            {activity.length ? (
                <div className="dashboard-activity-list">
                    {activity.map((item) => {
                        const Icon = iconFor(item.action);
                        return (
                            <div className="dashboard-activity-row" key={item.id}>
                                <span className="dashboard-row-icon"><Icon size={14} /></span>
                                <div className="dashboard-row-main">
                                    <strong>{item.action || "Activity"}</strong>
                                    <small>{item.details || `Opportunity #${item.entity_id}`}</small>
                                </div>
                                <span className="dashboard-activity-meta"><b>{item.user || "System"}</b><small>{formatDate(item.timestamp)}</small></span>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <EmptyState icon={Activity} message="No recent activity in your scope." />
            )}
        </Card>
    );
}
