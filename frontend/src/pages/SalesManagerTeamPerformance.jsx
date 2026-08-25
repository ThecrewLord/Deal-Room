import { useEffect, useMemo, useState } from "react";
import { ArrowRight, RefreshCw, Search, TrendingUp, Target, DollarSign, AlertTriangle, Percent } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getTeamPerformance } from "../api/managerPerformanceApi";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import KpiCard from "../components/ui/KpiCard";

const money = (value) => {
    const number = Number(value || 0);
    if (number >= 1000000) return `$${(number / 1000000).toFixed(1)}M`;
    if (number >= 1000) return `$${(number / 1000).toFixed(0)}K`;
    return `$${number.toLocaleString()}`;
};

export default function SalesManagerTeamPerformance() {
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        try { setLoading(true); setError(""); setData(await getTeamPerformance()); }
        catch (err) { setError(err?.response?.data?.message || "Unable to load team performance."); }
        finally { setLoading(false); }
    };
    useEffect(() => { load(); }, []);

    const employees = useMemo(() => (data?.employees || []).filter((e) => `${e.full_name} ${e.email}`.toLowerCase().includes(search.toLowerCase())), [data, search]);
    const totals = useMemo(() => (data?.employees || []).reduce((acc, employee) => {
        acc.pipeline += Number(employee.metrics?.pipeline_value || 0);
        acc.forecast += Number(employee.metrics?.weighted_forecast || 0);
        acc.won += Number(employee.metrics?.closed_won || 0);
        acc.stalled += Number(employee.metrics?.stalled_deals || 0);
        return acc;
    }, { pipeline: 0, forecast: 0, won: 0, stalled: 0 }), [data]);

    return <div className="standard-page manager-performance-page">
        <PageHeader title="Team Performance" description="Individual performance of the Sales Executives assigned to you." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14} /> Refresh</Button>} />
        {error && <div className="standard-error">{error}</div>}
        <div className="manager-performance-summary ui-kpi-grid-5">
            <KpiCard icon={UsersIcon} label="Team Members" value={data?.team_size ?? 0} description="Direct reports" />
            <KpiCard icon={DollarSign} label="Team Pipeline" value={money(totals.pipeline)} description="Open opportunities" />
            <KpiCard icon={TrendingUp} label="Weighted Forecast" value={money(totals.forecast)} description="Probability-adjusted" />
            <KpiCard icon={Target} label="Deals Won" value={totals.won} description="Closed won" />
            <KpiCard icon={AlertTriangle} label="Stalled Deals" value={totals.stalled} description={totals.stalled ? "Needs attention" : "No stalled deals"} />
        </div>
        <Card padding={false}>
            <div className="manager-performance-toolbar"><div className="ui-search"><Search size={15} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search employees…" /></div></div>
            {loading ? <div className="manager-loading">Loading team performance…</div> : !employees.length ? <div className="manager-empty">No employees match your search.</div> : <div className="manager-performance-table-wrap"><table className="ui-data-table manager-performance-table"><thead><tr><th>Employee</th><th>Pipeline</th><th>Forecast</th><th>Open deals</th><th>Won / Lost</th><th>Win rate</th><th>Stalled</th><th></th></tr></thead><tbody>{employees.map((employee) => <tr key={employee.user_id}><td><div className="manager-table-user"><span className="manager-avatar">{employee.full_name?.charAt(0)?.toUpperCase()}</span><span><strong>{employee.full_name}</strong><small>{employee.email}</small></span></div></td><td>{money(employee.metrics?.pipeline_value)}</td><td>{money(employee.metrics?.weighted_forecast)}</td><td>{employee.metrics?.open_opportunities ?? 0}</td><td>{employee.metrics?.closed_won ?? 0} / {employee.metrics?.closed_lost ?? 0}</td><td><span className="manager-win-rate"><Percent size={12} /> {employee.metrics?.win_rate ?? 0}%</span></td><td>{employee.metrics?.stalled_deals ?? 0}</td><td><Button variant="ghost" size="sm" onClick={() => navigate(`/sales-manager/team-performance/${employee.user_id}`)}>View <ArrowRight size={13} /></Button></td></tr>)}</tbody></table></div>}
        </Card>
    </div>;
}

function UsersIcon() { return <Target size={18} />; }
