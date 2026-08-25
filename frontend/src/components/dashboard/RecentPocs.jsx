import { CalendarDays, FlaskConical } from "lucide-react";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";

const formatDate = (value) => {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
};

export default function RecentPocs({ pocs = [], title = "Recent POCs", description = "Upcoming or active proof-of-concept work in scope." }) {
    return (
        <Card className="dashboard-list-card">
            <div className="dashboard-card-header">
                <div>
                    <h2>{title}</h2>
                    <p>{description}</p>
                </div>
            </div>
            {pocs.length ? (
                <div className="dashboard-poc-list">
                    {pocs.map((item) => (
                        <div className="dashboard-poc-row" key={item.id}>
                            <span className="dashboard-row-icon"><FlaskConical size={15} /></span>
                            <div className="dashboard-row-main">
                                <strong>{item.opportunity || "Opportunity"}</strong>
                                <small>{item.objective || "POC objective not provided"}</small>
                            </div>
                            <div className="dashboard-poc-meta">
                                <span>{item.status || "-"}</span>
                                <small><CalendarDays size={12} /> {formatDate(item.target_date)}</small>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <EmptyState message="No upcoming POCs in your scope." />
            )}
        </Card>
    );
}
