import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, BriefcaseBusiness, Clock3, FlaskConical, RefreshCw, Target, TrendingUp } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { getPreSalesEmployeePerformance } from "../api/preSalesPerformanceApi";
import PageHeader from "../components/ui/PageHeader";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import StageBadge from "../components/ui/StageBadge";
import StatusBadge from "../components/ui/StatusBadge";
import KpiCard from "../components/ui/KpiCard";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};
const initials = (name = "") => name.split(/\s+/).filter(Boolean).slice(0, 2).map(x => x[0]).join("").toUpperCase() || "U";

export default function PreSalesManagerEmployeePerformance() {
    const { employeeId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
    const load = async () => { try { setLoading(true); setError(""); setData(await getPreSalesEmployeePerformance(employeeId)); } catch (e) { setError(e?.response?.data?.message || "Unable to load employee performance."); } finally { setLoading(false); } };
    useEffect(() => { load(); }, [employeeId]);
    const pipeline = data?.pipeline_by_stage || [];
    const maxValue = Math.max(...pipeline.map(x => Number(x.value || 0)), 1);
    const pocStatuses = data?.poc_by_status || [];
    const maxPoc = Math.max(...pocStatuses.map(x => Number(x.count || 0)), 1);
    const m = data?.metrics || {};
    const e = data?.employee || {};
    const roleClass = e.role === "Solution Engineer" ? "technical" : "se";
    const performanceScore = useMemo(() => {
        const completed = Number(m.completed_pocs || 0); const active = Number(m.active_pocs || 0); const stalled = Number(m.stalled_opportunities || 0);
        return Math.max(0, Math.min(100, Math.round((completed * 25) + (active * 10) + Math.max(0, 20 - stalled * 5))));
    }, [m]);
    if (loading) return <div className="standard-page"><div className="psm-loading">Loading employee performance…</div></div>;
    return <div className="standard-page psm-performance-page fade-in">
        <PageHeader title={e.full_name || "Employee Performance"} description={`${e.role || "Technical Team Member"} · Individual performance and workload`} actions={<><Button variant="ghost" onClick={() => navigate("/pre-sales/team-performance")}><ArrowLeft size={14}/> Team Performance</Button><Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button></>} />
        {error && <div className="standard-error">{error}</div>}
        <div className="psm-profile-strip">
            <div className="psm-profile-avatar">{initials(e.full_name)}</div>
            <div className="psm-profile-identity"><h2>{e.full_name}</h2><p>{e.email}</p><em className={`psm-role-chip ${roleClass}`}>{e.role}</em></div>
            <div className="psm-score"><span>Technical workload score</span><strong>{performanceScore}</strong><small>Based on current POC workload and stalled work</small></div>
        </div>
        <div className="psm-performance-kpis detail ui-kpi-grid-5">
            <KpiCard icon={BriefcaseBusiness} label="Assigned Opportunities" value={m.assigned_opportunities || 0} description={`${money(m.assigned_value)} assigned value`} />
            <KpiCard icon={TrendingUp} label="Weighted Forecast" value={money(m.weighted_forecast)} description="Probability-adjusted" />
            <KpiCard icon={Clock3} label="Active Work" value={m.active_opportunities || 0} description={`${m.average_stage_age_days || 0}d avg. stage age`} />
            <KpiCard icon={FlaskConical} label="Active POCs" value={m.active_pocs || 0} description={`${m.completed_pocs || 0} completed`} />
            <KpiCard icon={Target} label="Stalled Work" value={m.stalled_opportunities || 0} description="Needs manager attention" />
        </div>
        <div className="psm-employee-detail-grid">
            <Card><div className="psm-card-head"><div><h3>Assigned Pipeline</h3><p>Opportunities where this employee is part of the technical team.</p></div></div><div className="psm-detail-stage-list">{pipeline.map((item, i) => <div className="psm-detail-stage" key={item.stage}><div><strong>{item.stage}</strong><span>{item.count} {item.count === 1 ? "deal" : "deals"}</span></div><div className="psm-detail-track"><i style={{width: `${Math.max(Number(item.value || 0) / maxValue * 100, item.count ? 4 : 0)}%`}} /></div><b>{money(item.value)}</b></div>)}</div></Card>
            <Card><div className="psm-card-head"><div><h3>POC Performance</h3><p>Current status across assigned opportunities.</p></div></div><div className="psm-poc-status-list">{pocStatuses.map(item => <div key={item.status}><span>{item.status}</span><div><i style={{width: `${Math.max(Number(item.count || 0) / maxPoc * 100, 5)}%`}} /></div><b>{item.count}</b></div>)}{!pocStatuses.length && <p className="psm-no-data">No POC activity yet.</p>}</div></Card>
        </div>
        <Card><div className="psm-card-head"><div><h3>Recent Technical Work</h3><p>Latest opportunities assigned to this team member.</p></div></div><div className="ui-table-wrap"><table className="ui-data-table"><thead><tr><th>Opportunity</th><th>Stage</th><th>Status</th><th>Value</th><th>Probability</th><th>Expected Close</th></tr></thead><tbody>{(data?.recent_work || []).map(item => <tr key={item.id}><td><strong>{item.name}</strong></td><td><StageBadge stage={item.stage}/></td><td><StatusBadge status={item.status}/></td><td>{money(item.value)}</td><td>{item.probability}%</td><td>{item.expected_close_date || "—"}</td></tr>)}{!(data?.recent_work || []).length && <tr><td colSpan="6" className="manager-empty-cell">No technical work available.</td></tr>}</tbody></table></div></Card>
    </div>;
}
