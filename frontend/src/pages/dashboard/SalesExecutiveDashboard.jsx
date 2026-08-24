import { useEffect, useState } from "react";
import { ArrowRight, AlertTriangle, DollarSign, Percent, RefreshCw, Target, TrendingUp } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getDashboardSummary } from "../../api/dashboardApi";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import PipelineOutcomePanel from "../../components/dashboard/PipelineOutcomePanel";
import PageHeader from "../../components/ui/PageHeader";

const money = (value) => { const n = Number(value || 0); if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`; if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`; return `$${n.toLocaleString()}`; };
const firstName = (name) => name?.trim()?.split(/\s+/)[0] || "there";

function Metric({ icon, label, value, hint }) { return <div className="exec-metric"><div className="exec-metric-icon">{icon}</div><span>{label}</span><strong>{value}</strong><small>{hint}</small></div>; }
export default function SalesExecutiveDashboard() {
    const { user } = useAuth(); const navigate = useNavigate();
    const [data, setData] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
    const load = async () => { try { setLoading(true); setError(""); setData(await getDashboardSummary()); } catch (err) { setError(err?.response?.data?.message || "Unable to load your dashboard."); } finally { setLoading(false); } };
    useEffect(() => { load(); }, []);
    if (loading) return <div className="standard-page"><div className="manager-loading">Loading your sales workspace…</div></div>;
    if (error) return <div className="standard-page"><div className="standard-error">{error}</div><Button onClick={load}>Retry</Button></div>;

    const pipeline = data?.pipeline_by_stage || []; const recent = data?.recent_opportunities || []; const open = Number(data?.open_opportunities || 0); const won = Number(data?.closed_won || 0); const lost = Number(data?.closed_lost || 0); const closed = won + lost;
    const inProgressPct = Number(data?.total_opportunities || 0) ? Math.round((open / Number(data.total_opportunities)) * 100) : 0;
    const winPct = closed ? Math.round((won / closed) * 100) : 0; const lossPct = closed ? Math.round((lost / closed) * 100) : 0;

    return <div className="standard-page exec-dashboard fade-in">
        <PageHeader title={`Good morning, ${firstName(user?.full_name)} 👋`} description="Your sales pipeline, performance and next actions in one place." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14} /> Refresh</Button>} />

        <div className="exec-kpi-grid">
            <Metric icon={<Target size={18} />} label="My Opportunities" value={data?.total_opportunities ?? 0} hint={`${open} currently open`} />
            <Metric icon={<DollarSign size={18} />} label="My Pipeline" value={money(data?.total_pipeline_value)} hint="Open pipeline value" />
            <Metric icon={<TrendingUp size={18} />} label="Weighted Forecast" value={money(data?.weighted_forecast)} hint="Probability-adjusted" />
            <Metric icon={<Percent size={18} />} label="Win Rate" value={`${winPct}%`} hint={`${won} won / ${closed} closed`} />
            <Metric icon={<AlertTriangle size={18} />} label="Stalled Deals" value={data?.stalled_deals ?? 0} hint={data?.stalled_deals ? "Needs attention" : "Pipeline is moving"} />
        </div>

        <PipelineOutcomePanel pipeline={pipeline} won={won} lost={lost} open={open} total={data?.total_opportunities || 0} />

        <Card className="exec-recent-card"><div className="exec-section-head"><div><h2>Recent Opportunities</h2><p>Your most recently updated opportunities.</p></div><Button variant="ghost" onClick={() => navigate("/opportunities")}>View all <ArrowRight size={14} /></Button></div>{recent.length ? <div className="exec-opportunity-list">{recent.map((o) => <button key={o.id} onClick={() => navigate(`/opportunity/${o.id}`)}><div className="exec-opportunity-main"><strong>{o.name}</strong><span>{o.account} · {o.stage}</span></div><div className="exec-opportunity-value"><strong>{money(o.value)}</strong><span>{o.probability}% probability</span></div><span className={`exec-status ${String(o.status || "").toLowerCase()}`}>{o.status}</span><ArrowRight size={15} /></button>)}</div> : <div className="exec-empty">No recently updated opportunities.</div>}</Card>
    </div>;
}
