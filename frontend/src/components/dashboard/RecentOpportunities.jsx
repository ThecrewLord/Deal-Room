import { ArrowRight, BriefcaseBusiness } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

export default function RecentOpportunities({ opportunities = [], title = "Recent Opportunities", description = "Recently updated opportunities in your authorized scope." }) {
    const navigate = useNavigate();
    return (
        <Card className="dashboard-list-card">
            <div className="dashboard-card-header">
                <div>
                    <h2>{title}</h2>
                    <p>{description}</p>
                </div>
                <button type="button" className="dashboard-text-button" onClick={() => navigate("/opportunities")}>View all <ArrowRight size={14} /></button>
            </div>
            {opportunities.length ? (
                <div className="dashboard-opportunity-list">
                    {opportunities.map((item) => (
                        <button key={item.id} type="button" className="dashboard-opportunity-row" onClick={() => navigate(`/opportunity/${item.id}`)}>
                            <span className="dashboard-row-icon"><BriefcaseBusiness size={15} /></span>
                            <span className="dashboard-row-main">
                                <strong>{item.name}</strong>
                                <small>{item.account || "-"} · {item.stage || "-"}</small>
                            </span>
                            <span className="dashboard-row-value">
                                <strong>{money(item.value)}</strong>
                                <small>{item.probability ?? 0}% probability</small>
                            </span>
                            <span className="dashboard-row-arrow"><ArrowRight size={15} /></span>
                        </button>
                    ))}
                </div>
            ) : (
                <EmptyState message="No recent opportunities in your scope." />
            )}
        </Card>
    );
}
