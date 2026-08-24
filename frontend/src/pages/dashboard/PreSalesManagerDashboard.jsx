import { useEffect, useState } from "react";
import { ArrowRight, AlertTriangle, CheckCircle2, Clock3, DollarSign, FlaskConical, RefreshCw, Target, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { getDashboardSummary } from "../../api/dashboardApi";
import { getPendingPreSalesAssignments } from "../../api/preSalesAssignmentApi";
import PageHeader from "../../components/ui/PageHeader";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import PipelineOutcomePanel from "../../components/dashboard/PipelineOutcomePanel";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

function Metric({ icon, label, value, hint }) {
    return <div className="psm-metric"><span className="psm-metric-icon">{icon}</span><div><span>{label}</span><strong>{value}</strong><small>{hint}</small></div></div>;
}

function QueueCard({ icon, title, count, description, action, onClick }) {
    return <button type="button" className="psm-queue-card" onClick={onClick}>
        <span className="psm-queue-icon">{icon}</span>
        <span className="psm-queue-copy"><strong>{title}</strong><b>{count}</b><small>{description}</small></span>
        <span className="psm-queue-link">{action}<ArrowRight size={14} /></span>
    </button>;
}

export default function PreSalesManagerDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [dashboard, setDashboard] = useState(null);
    const [assignments, setAssignments] = useState([]);
    
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        try {
            setLoading(true); setError("");
            const [summary, assignmentQueue] = await Promise.all([
                getDashboardSummary(), getPendingPreSalesAssignments(),
            ]);
            setDashboard(summary || {});
            setAssignments(assignmentQueue || []);
            
        } catch (e) {
            setError(e?.response?.data?.message || "Unable to load Pre-Sales Manager dashboard.");
        } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const pipeline = dashboard?.pipeline_by_stage || [];
    const totalOpportunities = Number(dashboard?.total_opportunities || 0);
    const openOpportunities = Number(dashboard?.open_opportunities || 0);
    const closedWon = Number(dashboard?.closed_won || 0);
    const closedLost = Number(dashboard?.closed_lost || 0);
    const closed = closedWon + closedLost;
    const firstName = user?.full_name?.trim()?.split(/\s+/)[0] || "there";

    if (loading) return <div className="psm-page"><div className="psm-loading">Loading Pre-Sales Manager workspace…</div></div>;
    if (error) return <div className="psm-page"><PageHeader title="Pre-Sales Manager" description="Technical delivery oversight and pipeline health." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14}/> Retry</Button>}/><div className="standard-error">{error}</div></div>;

    return <div className="psm-page fade-in">
        <PageHeader title={`Good morning, ${firstName} 👋`} description="Technical delivery oversight, POC governance and pipeline health." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button>} />

        <div className="psm-kpi-grid">
            <Metric icon={<Target size={17}/>} label="Total Opportunities" value={totalOpportunities} hint={`${openOpportunities} currently open`} />
            <Metric icon={<DollarSign size={17}/>} label="Pipeline Value" value={money(dashboard?.total_pipeline_value)} hint="Open pipeline" />
            <Metric icon={<FlaskConical size={17}/>} label="Active POCs" value={dashboard?.active_pocs ?? 0} hint="Technical evaluations" />
            <Metric icon={<Clock3 size={17}/>} label="Avg. Stage Age" value={`${dashboard?.average_stage_ageing ?? 0} days`} hint="Pipeline ageing" />
            <Metric icon={<AlertTriangle size={17}/>} label="Stalled Deals" value={dashboard?.stalled_deals ?? 0} hint={Number(dashboard?.stalled_deals || 0) ? "Needs attention" : "No stalled deals"} />
        </div>

        <div className="psm-queue-grid">
            <QueueCard icon={<Users size={18}/>} title="Pending Technical Assignments" count={assignments.length} description="Opportunities awaiting Solution Engineer allocation." action="Open queue" onClick={() => navigate("/pre-sales/assignments")} />
        </div>

        <div className="psm-section-title"><div><h2>Pipeline Overview</h2><p>Overall technical pipeline and deal outcomes.</p></div><span>{money(dashboard?.weighted_forecast)} weighted forecast</span></div>

        <PipelineOutcomePanel pipeline={pipeline} won={closedWon} lost={closedLost} open={openOpportunities} total={totalOpportunities} />

        <div className="psm-lower-grid">
        </div>
    </div>;
}
