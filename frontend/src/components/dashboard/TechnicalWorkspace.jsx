import { ArrowRight, FlaskConical, Target } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";
import ErrorState from "../ui/ErrorState";

export default function TechnicalWorkspace({ opportunities = [], pocs = [], error = "", onRetry }) {
    const navigate = useNavigate();
    return (
        <Card className="dashboard-workspace-card">
            <div className="dashboard-card-header">
                <div>
                    <h2>Technical Workspace</h2>
                    <p>Assigned opportunities and POC work for the Solution Engineer role.</p>
                </div>
            </div>
            {error ? <ErrorState message={error} onRetry={onRetry} /> : (
                <div className="dashboard-workspace-grid">
                    <div>
                        <div className="dashboard-subsection-title"><span><Target size={14} /> Assigned Opportunities</span><b>{opportunities.length}</b></div>
                        {opportunities.length ? opportunities.slice(0, 6).map((item) => (
                            <button key={item.id} type="button" className="dashboard-work-item" onClick={() => navigate(`/opportunity/${item.id}`)}>
                                <span><strong>{item.name}</strong><small>{item.account || "-"} · {item.stage || "-"}</small></span>
                                <ArrowRight size={14} />
                            </button>
                        )) : <EmptyState message="No assigned opportunities." />}
                    </div>
                    <div>
                        <div className="dashboard-subsection-title"><span><FlaskConical size={14} /> POCs Requiring Attention</span><b>{pocs.length}</b></div>
                        {pocs.length ? pocs.slice(0, 6).map((item) => (
                            <button key={item.id} type="button" className="dashboard-work-item" onClick={() => item.opportunity_id ? navigate(`/opportunity/${item.opportunity_id}`) : undefined}>
                                <span><strong>{item.objective || item.opportunity || "POC"}</strong><small>{item.opportunity || "-"} · {item.status || "-"}</small></span>
                                <ArrowRight size={14} />
                            </button>
                        )) : <EmptyState message="No active POCs require attention." />}
                    </div>
                </div>
            )}
        </Card>
    );
}
