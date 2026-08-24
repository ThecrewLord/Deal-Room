import { useEffect, useState } from "react";
import { ArrowRight, DollarSign, Target, TrendingUp, Users, AlertTriangle, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getDashboardSummary } from "../../api/dashboardApi";
import { getTeamPerformance } from "../../api/managerPerformanceApi";
import { useAuth } from "../../context/AuthContext";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import PageHeader from "../../components/ui/PageHeader";
import PipelineOutcomePanel from "../../components/dashboard/PipelineOutcomePanel";

const money = (value) => {
    const number = Number(value || 0);
    if (number >= 1000000) return `$${(number / 1000000).toFixed(1)}M`;
    if (number >= 1000) return `$${(number / 1000).toFixed(0)}K`;
    return `$${number.toLocaleString()}`;
};

const firstName = (name) => name?.trim()?.split(/\s+/)[0] || "there";

function Metric({ icon, label, value, hint }) {
    return (
        <div className="manager-metric">
            <div className="manager-metric-icon">{icon}</div>
            <div>
                <span>{label}</span>
                <strong>{value}</strong>
                <small>{hint}</small>
            </div>
        </div>
    );
}

export default function SalesManagerDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [dashboard, setDashboard] = useState(null);
    const [team, setTeam] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        try {
            setLoading(true);
            setError("");
            const [summary, performance] = await Promise.all([
                getDashboardSummary(),
                getTeamPerformance(),
            ]);
            setDashboard(summary);
            setTeam(performance);
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load Sales Manager dashboard.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    if (loading) return <div className="standard-page"><div className="manager-loading">Loading your manager dashboard…</div></div>;
    if (error) return <div className="standard-page"><div className="standard-error">{error}</div><Button onClick={load}>Retry</Button></div>;

    const employees = team?.employees || [];
    const totalPipeline = employees.reduce((sum, e) => sum + Number(e.metrics?.pipeline_value || 0), 0);
    const totalForecast = employees.reduce((sum, e) => sum + Number(e.metrics?.weighted_forecast || 0), 0);
    const totalWon = employees.reduce((sum, e) => sum + Number(e.metrics?.closed_won || 0), 0);
    const stalled = employees.reduce((sum, e) => sum + Number(e.metrics?.stalled_deals || 0), 0);

    return (
        <div className="standard-page manager-dashboard fade-in">
            <PageHeader
                title={`Good morning, ${firstName(user?.full_name)} 👋`}
                description="Sales performance, team health and pipeline at a glance."
                actions={<Button variant="secondary" onClick={load}><RefreshCw size={14} /> Refresh</Button>}
            />

            <div className="manager-kpi-grid">
                <Metric icon={<Users size={18} />} label="Team Members" value={team?.team_size ?? 0} hint="Direct reports" />
                <Metric icon={<DollarSign size={18} />} label="Team Pipeline" value={money(totalPipeline)} hint="Owned open pipeline" />
                <Metric icon={<TrendingUp size={18} />} label="Weighted Forecast" value={money(totalForecast)} hint="Probability-adjusted" />
                <Metric icon={<Target size={18} />} label="Deals Won" value={totalWon} hint={`${dashboard?.conversion_rate ?? 0}% overall conversion`} />
                <Metric icon={<AlertTriangle size={18} />} label="Stalled Deals" value={stalled} hint={stalled ? "Needs attention" : "No stalled deals"} />
            </div>

            <PipelineOutcomePanel
                pipeline={dashboard?.pipeline_by_stage || []}
                won={dashboard?.closed_won ?? totalWon}
                lost={dashboard?.closed_lost ?? 0}
                open={dashboard?.open_opportunities ?? 0}
                total={dashboard?.total_opportunities ?? 0}
            />

            <div className="manager-dashboard-grid">
                <Card className="manager-team-card">
                    <div className="manager-section-head">
                        <div><h2>Team Performance</h2><p>Compare each Sales Executive on the metrics that matter.</p></div>
                        <Button variant="ghost" onClick={() => navigate("/sales-manager/team-performance")}>View full performance <ArrowRight size={14} /></Button>
                    </div>
                    <div className="manager-employee-list">
                        {employees.map((employee) => {
                            const pipeline = Number(employee.metrics?.pipeline_value || 0);
                            const winRate = Number(employee.metrics?.win_rate || 0);
                            return (
                                <button className="manager-employee-row" key={employee.user_id} onClick={() => navigate(`/sales-manager/team-performance/${employee.user_id}`)}>
                                    <span className="manager-avatar">{employee.full_name?.charAt(0)?.toUpperCase()}</span>
                                    <span className="manager-employee-main"><strong>{employee.full_name}</strong><small>{employee.email}</small></span>
                                    <span className="manager-employee-stat"><small>Pipeline</small><strong>{money(pipeline)}</strong></span>
                                    <span className="manager-employee-stat"><small>Win rate</small><strong>{winRate}%</strong></span>
                                    <span className="manager-employee-stat"><small>Open deals</small><strong>{employee.metrics?.open_opportunities ?? 0}</strong></span>
                                    <ArrowRight size={15} />
                                </button>
                            );
                        })}
                        {!employees.length && <div className="manager-empty">No active Sales Executives are assigned to you yet.</div>}
                    </div>
                </Card>

            </div>

            <div className="manager-dashboard-grid manager-dashboard-grid-bottom">
                <Card>
                    <div className="manager-section-head"><div><h2>Manager Snapshot</h2><p>Your overall sales pipeline scope.</p></div></div>
                    <div className="manager-snapshot-grid">
                        <div><span>Total opportunities</span><strong>{dashboard?.total_opportunities ?? 0}</strong></div>
                        <div><span>Open opportunities</span><strong>{dashboard?.open_opportunities ?? 0}</strong></div>
                        <div><span>Pipeline value</span><strong>{money(dashboard?.total_pipeline_value)}</strong></div>
                        <div><span>Stalled deals</span><strong>{dashboard?.stalled_deals ?? 0}</strong></div>
                    </div>
                </Card>
                <Card>
                    <div className="manager-section-head"><div><h2>Review Queue</h2><p>Opportunities waiting for your decision.</p></div></div>
                    <div className="manager-review-cta"><div><strong>Review submitted opportunities</strong><span>Approve and assign a Sales Owner, or reject with a reason.</span></div><Button onClick={() => navigate("/sales-manager/review")}>Open queue <ArrowRight size={14} /></Button></div>
                </Card>
            </div>
        </div>
    );
}
