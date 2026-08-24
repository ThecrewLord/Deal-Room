import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, DollarSign, RefreshCw, Target, TrendingUp, AlertTriangle, Percent } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { getEmployeePerformance } from "../api/managerPerformanceApi";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import StageBadge from "../components/ui/StageBadge";
import StatusBadge from "../components/ui/StatusBadge";

const money = (value) => {
    const number = Number(value || 0);
    if (number >= 1000000) return `$${(number / 1000000).toFixed(1)}M`;
    if (number >= 1000) return `$${(number / 1000).toFixed(0)}K`;
    return `$${number.toLocaleString()}`;
};

export default function SalesManagerEmployeePerformance() {
    const { employeeId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        try { setLoading(true); setError(""); setData(await getEmployeePerformance(employeeId)); }
        catch (err) { setError(err?.response?.data?.message || "Unable to load employee performance."); }
        finally { setLoading(false); }
    };
    useEffect(() => { load(); }, [employeeId]);

    if (loading) return <div className="standard-page"><div className="manager-loading">Loading employee performance…</div></div>;
    if (error) return <div className="standard-page"><div className="standard-error">{error}</div><Button onClick={load}>Retry</Button></div>;

    const m = data?.metrics || {};
    const pipeline = data?.pipeline_by_stage || [];
    const maxStageValue = Math.max(...pipeline.map((item) => Number(item.value || 0)), 1);

    return <div className="standard-page manager-employee-page">
        <PageHeader title={data?.employee?.full_name || "Employee Performance"} description={`${data?.employee?.email || ""} · Individual Sales Executive performance`} actions={<><Button variant="ghost" onClick={() => navigate("/sales-manager/team-performance")}><ArrowLeft size={14} /> Back to team</Button><Button variant="secondary" onClick={load}><RefreshCw size={14} /> Refresh</Button></>} />
        <div className="manager-profile-strip"><span className="manager-avatar manager-avatar-large">{data?.employee?.full_name?.charAt(0)?.toUpperCase()}</span><div><strong>{data?.employee?.full_name}</strong><span>{data?.employee?.email}</span></div><StatusBadge status="Active" /></div>
        <div className="manager-kpi-grid manager-kpi-grid-detail">
            <DetailMetric icon={<DollarSign size={18} />} label="Pipeline" value={money(m.pipeline_value)} hint="Owned open pipeline" />
            <DetailMetric icon={<TrendingUp size={18} />} label="Weighted forecast" value={money(m.weighted_forecast)} hint="Probability-adjusted" />
            <DetailMetric icon={<Target size={18} />} label="Open deals" value={m.open_opportunities ?? 0} hint={`${m.total_opportunities ?? 0} total opportunities`} />
            <DetailMetric icon={<Percent size={18} />} label="Win rate" value={`${m.win_rate ?? 0}%`} hint={`${m.closed_won ?? 0} won · ${m.closed_lost ?? 0} lost`} />
            <DetailMetric icon={<AlertTriangle size={18} />} label="Stalled" value={m.stalled_deals ?? 0} hint={`${m.average_stage_age_days ?? 0} day avg stage age`} />
        </div>
        <div className="manager-dashboard-grid">
            <Card><div className="manager-section-head"><div><h2>Pipeline by Stage</h2><p>Current owned pipeline distribution.</p></div></div><div className="manager-bar-list manager-stage-list">{pipeline.map((item) => { const value = Number(item.value || 0); return <div className="manager-bar-row" key={item.stage}><div className="manager-bar-label"><span>{item.stage}</span><strong>{money(value)} · {item.count}</strong></div><div className="manager-bar-track"><div className="manager-bar-fill" style={{ width: `${Math.max((value / maxStageValue) * 100, value ? 4 : 0)}%` }} /></div></div>; })}</div></Card>
            <Card><div className="manager-section-head"><div><h2>Performance Signals</h2><p>Metrics worth discussing in the next 1:1.</p></div></div><div className="manager-signal-list"><Signal label="Average deal value" value={money(m.average_deal_value)} /><Signal label="Average stage age" value={`${m.average_stage_age_days ?? 0} days`} /><Signal label="Stalled deals" value={m.stalled_deals ?? 0} warn={m.stalled_deals > 0} /><Signal label="Unassigned submissions" value={m.unassigned_submissions ?? 0} /></div></Card>
        </div>
        <Card padding={false}><div className="manager-section-head manager-section-head-pad"><div><h2>Recent Opportunities</h2><p>Most recently updated opportunities owned by this employee.</p></div></div><div className="manager-performance-table-wrap"><table className="ui-data-table"><thead><tr><th>Opportunity</th><th>Stage</th><th>Status</th><th>Value</th><th>Probability</th><th>Expected close</th><th></th></tr></thead><tbody>{(data?.recent_opportunities || []).map((o) => <tr key={o.id}><td><strong>{o.name}</strong></td><td><StageBadge stage={o.stage} /></td><td><StatusBadge status={o.status} /></td><td>{money(o.value)}</td><td>{o.probability}%</td><td>{o.expected_close_date || "—"}</td><td><Button variant="ghost" size="sm" onClick={() => navigate(`/opportunity/${o.id}`)}>Open <ArrowRight size={13} /></Button></td></tr>)}{!(data?.recent_opportunities || []).length && <tr><td colSpan="7" className="manager-empty-cell">No opportunities assigned yet.</td></tr>}</tbody></table></div></Card>
    </div>;
}

function DetailMetric({ icon, label, value, hint }) { return <div className="manager-metric"><div className="manager-metric-icon">{icon}</div><div><span>{label}</span><strong>{value}</strong><small>{hint}</small></div></div>; }
function Signal({ label, value, warn }) { return <div className={`manager-signal ${warn ? "warn" : ""}`}><span>{label}</span><strong>{value}</strong></div>; }
