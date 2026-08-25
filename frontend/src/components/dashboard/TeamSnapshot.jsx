import { ArrowRight, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

export default function TeamSnapshot({ team, error = "", loading = false, onRetry, role = "Sales" }) {
    const navigate = useNavigate();
    const employees = team?.employees || [];
    const path = role === "Pre-Sales Manager" ? "/pre-sales/team-performance" : "/sales-manager/team-performance";
    const detailPath = role === "Pre-Sales Manager" ? (id) => `/pre-sales/team-performance/${id}` : (id) => `/sales-manager/team-performance/${id}`;
    return (
        <Card className="dashboard-team-card">
            <div className="dashboard-card-header">
                <div>
                    <h2>Team Performance</h2>
                    <p>{role === "Pre-Sales Manager" ? "Technical workload across your direct reports." : "Sales performance across your direct reports."}</p>
                </div>
                <button type="button" className="dashboard-text-button" onClick={() => navigate(path)}>View full performance <ArrowRight size={14} /></button>
            </div>
            {error ? <ErrorState message={error} onRetry={onRetry} /> : loading ? <LoadingState message="Loading team performance…" compact /> : employees.length ? (
                <div className="dashboard-team-list">
                    {employees.slice(0, 6).map((employee) => {
                        const metrics = employee.metrics || {};
                        return (
                            <button key={employee.user_id} type="button" className="dashboard-team-row" onClick={() => navigate(detailPath(employee.user_id))}>
                                <span className="dashboard-team-avatar">{String(employee.full_name || "U").split(/\s+/).map((x) => x[0]).slice(0, 2).join("").toUpperCase()}</span>
                                <span className="dashboard-row-main"><strong>{employee.full_name || "Team member"}</strong><small>{employee.email || ""}</small></span>
                                <span className="dashboard-team-stat"><small>Pipeline</small><strong>{money(metrics.pipeline_value ?? metrics.assigned_value)}</strong></span>
                                <span className="dashboard-team-stat"><small>{role === "Pre-Sales Manager" ? "Active POCs" : "Win rate"}</small><strong>{role === "Pre-Sales Manager" ? (metrics.active_pocs ?? 0) : `${metrics.win_rate ?? 0}%`}</strong></span>
                                <ArrowRight size={14} />
                            </button>
                        );
                    })}
                </div>
            ) : <EmptyState icon={Users} message="No direct reports are available." />}
        </Card>
    );
}
