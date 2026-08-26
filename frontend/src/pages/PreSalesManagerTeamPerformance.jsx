import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BarChart3, BriefcaseBusiness, Clock3, FlaskConical, RefreshCw, Search, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/ui/PageHeader";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import { getPreSalesTeamPerformance } from "../api/preSalesPerformanceApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import KpiCard from "../components/ui/KpiCard";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

const initials = (name = "") => name.split(/\s+/).filter(Boolean).slice(0, 2).map(x => x[0]).join("").toUpperCase() || "U";

export default function PreSalesManagerTeamPerformance() {
    const { activeRole } = useAuth();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [search, setSearch] = useState("");
    const [role, setRole] = useState("All");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        try { setLoading(true); setError(""); setData(await getPreSalesTeamPerformance()); }
        catch (e) { setError(e?.response?.data?.message || "Unable to load technical team performance."); }
        finally { setLoading(false); }
    };
    useEffect(() => { if (activeRole === ROLES.PRE_SALES_MANAGER) load(); }, [activeRole]);

    const employees = useMemo(() => {
        const q = search.trim().toLowerCase();
        return (data?.employees || []).filter(item => {
            const employee = item.employee || {};
            return (!q || `${employee.full_name} ${employee.email}`.toLowerCase().includes(q)) && (role === "All" || employee.role === role);
        });
    }, [data, search, role]);

    const summary = useMemo(() => {
        const rows = data?.employees || [];
        return {
            assigned: rows.reduce((s, x) => s + Number(x.metrics?.assigned_opportunities || 0), 0),
            active: rows.reduce((s, x) => s + Number(x.metrics?.active_opportunities || 0), 0),
            pocs: rows.reduce((s, x) => s + Number(x.metrics?.active_pocs || 0), 0),
            completed: rows.reduce((s, x) => s + Number(x.metrics?.completed_pocs || 0), 0),
        };
    }, [data]);

    if (activeRole !== ROLES.PRE_SALES_MANAGER) return <div className="standard-page"><PageHeader title="Team Performance" description="You do not have access to this page." /></div>;
    if (loading) return <div className="standard-page"><div className="psm-loading">Loading technical team performance…</div></div>;
    return <div className="standard-page psm-performance-page fade-in">
        <PageHeader title="Team Performance" description="Monitor the technical workload and POC performance of your Solution Engineer team." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button>} />
        {error && <div className="standard-error">{error}</div>}

        <div className="psm-performance-kpis ui-kpi-grid-5">
            <KpiCard icon={Users} label="Technical Team" value={data?.team_size || 0} description="Direct technical reports" />
            <KpiCard icon={BriefcaseBusiness} label="Assigned Opportunities" value={summary.assigned} description="Current technical scope" />
            <KpiCard icon={Clock3} label="Active Technical Work" value={summary.active} description="Open assigned work" />
            <KpiCard icon={FlaskConical} label="Active POCs" value={summary.pocs} description="Technical evaluations" />
            <KpiCard icon={BarChart3} label="Completed POCs" value={summary.completed} description="Completed evaluations" />
        </div>

        <Card padding={false} className="psm-performance-card">
            <div className="psm-performance-toolbar">
                <div><h2>Technical Team</h2><p>Each person below is a direct report of this Pre-Sales Manager.</p></div>
                <div className="psm-performance-filters"><label className="ui-search"><Search size={14}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search employees…" /></label><select value={role} onChange={e => setRole(e.target.value)}><option>All</option><option>Solution Engineer</option></select></div>
            </div>
            <div className="psm-team-table">
                <div className="psm-team-row psm-team-head"><span>Employee</span><span>Role</span><span>Assigned</span><span>Active</span><span>Active POCs</span><span>Avg. Stage Age</span><span></span></div>
                {employees.map(item => { const e = item.employee; const m = item.metrics || {}; return <button type="button" key={e.user_id} className="psm-team-row psm-team-data" onClick={() => navigate(`/pre-sales/team-performance/${e.user_id}`)}>
                    <span className="psm-employee-cell"><i>{initials(e.full_name)}</i><b>{e.full_name}</b><small>{e.email}</small></span>
                    <span><em className="psm-role-chip se">Solution Engineer</em></span>
                    <span><strong>{m.assigned_opportunities || 0}</strong><small>{money(m.assigned_value)}</small></span>
                    <span><strong>{m.active_opportunities || 0}</strong><small>{m.stalled_opportunities || 0} stalled</small></span>
                    <span><strong>{m.active_pocs || 0}</strong><small>{m.completed_pocs || 0} completed</small></span>
                    <span><strong>{m.average_stage_age_days || 0}d</strong><small>current workload</small></span>
                    <span className="psm-row-arrow"><ArrowRight size={16}/></span>
                </button>; })}
                {!employees.length && <EmptyState message={(data?.employees || []).length ? "No team members match your filters." : "No direct technical reports are assigned to you."}/>} 
            </div>
        </Card>
    </div>;
}
