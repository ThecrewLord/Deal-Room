import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, BriefcaseBusiness, DollarSign, FlaskConical, Percent, Target, TrendingUp, Users, Clock3 } from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ROLES } from "../../auth/roles";
import { getDashboardSummary } from "../../api/dashboardApi";
import { getTeamPerformance } from "../../api/managerPerformanceApi";
import { getPreSalesTeamPerformance } from "../../api/preSalesPerformanceApi";
import { getPendingPreSalesAssignments } from "../../api/preSalesAssignmentApi";
import adminApi from "../../api/adminApi";
import DashboardShell from "../../components/dashboard/DashboardShell";
import DashboardKpiRow from "../../components/dashboard/DashboardKpiRow";
import PipelineOutcomePanel from "../../components/dashboard/PipelineOutcomePanel";
import RecentOpportunities from "../../components/dashboard/RecentOpportunities";
import RecentPocs from "../../components/dashboard/RecentPocs";
import RecentActivity from "../../components/dashboard/RecentActivity";
import TechnicalWorkspace from "../../components/dashboard/TechnicalWorkspace";
import TeamSnapshot from "../../components/dashboard/TeamSnapshot";
import Card from "../../components/ui/Card";
import LoadingState from "../../components/ui/LoadingState";
import ErrorState from "../../components/ui/ErrorState";
import EmptyState from "../../components/ui/EmptyState";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

const buildBusinessKpis = (role, data, team, assignments) => {
    const common = {
        opportunities: Number(data?.total_opportunities || 0),
        pipeline: Number(data?.total_pipeline_value || 0),
        forecast: Number(data?.weighted_forecast || 0),
        open: Number(data?.open_opportunities || 0),
        won: Number(data?.closed_won || 0),
        stalled: Number(data?.stalled_deals || 0),
        activePocs: Number(data?.active_pocs || 0),
    };

    if (role === ROLES.SALES_EXECUTIVE) {
        const closed = common.won + Number(data?.closed_lost || 0);
        const winRate = closed ? Math.round((common.won / closed) * 100) : 0;
        return [
            { label: "My Opportunities", value: common.opportunities, description: `${common.open} currently open`, icon: Target },
            { label: "My Open Pipeline", value: money(common.pipeline), description: "Authorized open pipeline", icon: DollarSign },
            { label: "Weighted Forecast", value: money(common.forecast), description: "Probability-adjusted", icon: TrendingUp },
            { label: "Win Rate", value: `${winRate}%`, description: `${common.won} won of ${closed} closed`, icon: Percent },
            { label: "Stalled Deals", value: common.stalled, description: common.stalled ? "Needs attention" : "Pipeline is moving", icon: AlertTriangle },
        ];
    }

    if (role === ROLES.SOLUTION_ENGINEER) {
        return [
            { label: "Assigned Opportunities", value: common.opportunities, description: `${common.open} currently active`, icon: BriefcaseBusiness },
            { label: "Technical Pipeline", value: money(common.pipeline), description: "Assigned technical scope", icon: DollarSign },
            { label: "Weighted Forecast", value: money(common.forecast), description: "Probability-adjusted", icon: TrendingUp },
            { label: "Active POCs", value: common.activePocs, description: "Technical evaluations", icon: FlaskConical },
            { label: "Stalled Work", value: common.stalled, description: common.stalled ? "Needs attention" : "No stalled work", icon: AlertTriangle },
        ];
    }

    if (role === ROLES.SALES_MANAGER) {
        return [
            { label: "Team Members", value: team?.team_size ?? "—", description: "Direct reports", icon: Users },
            { label: "Team Pipeline", value: money(common.pipeline), description: `${common.open} open opportunities`, icon: DollarSign },
            { label: "Weighted Forecast", value: money(common.forecast), description: "Probability-adjusted", icon: TrendingUp },
            { label: "Deals Won", value: common.won, description: `${common.opportunities} opportunities in scope`, icon: Target },
            { label: "Stalled Deals", value: common.stalled, description: common.stalled ? "Needs attention" : "No stalled deals", icon: AlertTriangle },
        ];
    }

    if (role === ROLES.PRE_SALES_MANAGER) {
        return [
            { label: "Technical Team", value: team?.team_size ?? "—", description: "Direct technical reports", icon: Users },
            { label: "Technical Pipeline", value: money(common.pipeline), description: `${common.open} open opportunities`, icon: DollarSign },
            { label: "Weighted Forecast", value: money(common.forecast), description: "Probability-adjusted", icon: TrendingUp },
            { label: "Active POCs", value: common.activePocs, description: "Technical evaluations", icon: FlaskConical },
            { label: "Pending Assignments", value: assignments?.length ?? "—", description: "Awaiting Solution Engineer allocation", icon: Clock3 },
        ];
    }

    return [];
};

function BusinessDashboard({ user, role }) {
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [team, setTeam] = useState(null);
    const [teamError, setTeamError] = useState("");
    const [teamLoading, setTeamLoading] = useState(false);
    const [assignments, setAssignments] = useState(null);
    const [assignmentError, setAssignmentError] = useState("");
    const [assignmentLoading, setAssignmentLoading] = useState(false);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");

    const load = async ({ refresh = false } = {}) => {
        if (refresh) setRefreshing(true); else setLoading(true);
        setError("");
        try {
            const summary = await getDashboardSummary();
            setData(summary || {});
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load dashboard.");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }

        if (role === ROLES.SALES_MANAGER) {
            setTeamLoading(true);
            try {
                setTeamError("");
                setTeam(await getTeamPerformance());
            } catch (err) {
                setTeamError(err?.response?.data?.message || "Unable to load team performance.");
                setTeam(null);
            } finally {
                setTeamLoading(false);
            }
        }

        if (role === ROLES.PRE_SALES_MANAGER) {
            setTeamLoading(true);
            setAssignmentLoading(true);
            try {
                setTeamError("");
                setTeam(await getPreSalesTeamPerformance());
            } catch (err) {
                setTeamError(err?.response?.data?.message || "Unable to load technical team performance.");
                setTeam(null);
            } finally {
                setTeamLoading(false);
            }
            try {
                setAssignmentError("");
                setAssignments(await getPendingPreSalesAssignments() || []);
            } catch (err) {
                setAssignmentError(err?.response?.data?.message || "Unable to load pending technical assignments.");
                setAssignments(null);
            } finally {
                setAssignmentLoading(false);
            }
        }
    };

    useEffect(() => {
        load();
    }, [role]);

    const kpis = useMemo(() => buildBusinessKpis(role, data, team, assignments), [role, data, team, assignments]);
    const pipeline = data?.pipeline_by_stage || [];
    const recentOpportunities = data?.recent_opportunities || [];
    const recentPocs = data?.upcoming_pocs || [];
    const recentActivity = data?.recent_activity || [];
    const won = Number(data?.closed_won || 0);
    const lost = Number(data?.closed_lost || 0);
    const open = Number(data?.open_opportunities || 0);
    const total = Number(data?.total_opportunities || 0);

    if (loading) return <div className="deal-dashboard"><LoadingState message="Loading dashboard…" /></div>;
    if (error) return <div className="deal-dashboard"><ErrorState message={error} onRetry={() => load()} /></div>;

    return (
        <DashboardShell
            user={user}
            role={role}
            description={
                role === ROLES.SALES_EXECUTIVE
                    ? "Your sales pipeline, forecast and active opportunities."
                    : role === ROLES.SOLUTION_ENGINEER
                        ? "Your assigned technical workload, pipeline and POC activity."
                        : role === ROLES.SALES_MANAGER
                            ? "Team sales performance, pipeline health and review workload."
                            : "Technical team workload, pipeline health and assignment coverage."
            }
            onRefresh={() => load({ refresh: true })}
            refreshing={refreshing}
        >
            <DashboardKpiRow items={kpis} />

            <PipelineOutcomePanel pipeline={pipeline} won={won} lost={lost} open={open} total={total} />

            {role === ROLES.SOLUTION_ENGINEER && (
                <TechnicalWorkspace
                    opportunities={recentOpportunities}
                    pocs={recentPocs}
                />
            )}

            {role === ROLES.SALES_MANAGER && (
                <TeamSnapshot team={team} error={teamError} loading={teamLoading} onRetry={() => load()} role="Sales Manager" />
            )}

            {role === ROLES.PRE_SALES_MANAGER && (
                <>
                    <TeamSnapshot team={team} error={teamError} loading={teamLoading} onRetry={() => load()} role="Pre-Sales Manager" />
                    <Card className="dashboard-queue-card">
                        <div className="dashboard-card-header">
                            <div>
                                <h2>Pending Technical Assignments</h2>
                                <p>Approved opportunities awaiting Solution Engineer allocation.</p>
                            </div>
                            <button type="button" className="dashboard-text-button" onClick={() => navigate("/pre-sales/assignments")}>Open queue <span>→</span></button>
                        </div>
                        {assignmentError ? <ErrorState message={assignmentError} onRetry={() => load()} /> : assignmentLoading ? <LoadingState message="Loading assignment queue…" compact /> : assignments?.length ? (
                            <div className="dashboard-assignment-list">
                                {assignments.slice(0, 5).map((item) => (
                                    <div className="dashboard-assignment-row" key={item.opportunity_id}>
                                        <span className="dashboard-row-main"><strong>{item.opportunity_name}</strong><small>{item.account_name || "-"} · {item.sales_owner?.full_name || "Unassigned"}</small></span>
                                        <strong>{money(item.estimated_value)}</strong>
                                    </div>
                                ))}
                            </div>
                        ) : <EmptyState message="No opportunities are awaiting technical assignment." />}
                    </Card>
                </>
            )}

            <div className="dashboard-lower-grid">
                <RecentOpportunities opportunities={recentOpportunities} />
                {role === ROLES.SALES_EXECUTIVE ? (
                    <RecentPocs pocs={recentPocs} title="Recent POCs / Activity" description="POC work and target dates in your scope." />
                ) : (
                    <RecentActivity activity={recentActivity} />
                )}
            </div>
        </DashboardShell>
    );
}

function AdminDashboard() {
    const { user } = useAuth();
    const [users, setUsers] = useState([]);
    const [pending, setPending] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        setLoading(true);
        setError("");
        try {
            const [allUsers, pendingUsers] = await Promise.all([adminApi.getUsers(), adminApi.getPending()]);
            setUsers(Array.isArray(allUsers) ? allUsers : []);
            setPending(Array.isArray(pendingUsers) ? pendingUsers : []);
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load administration data.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, []);

    const stats = useMemo(() => {
        const approved = users.filter((item) => item.status === "APPROVED");
        const revoked = users.filter((item) => item.status === "REVOKED");
        return {
            total: users.length,
            active: approved.filter((item) => item.active).length,
            pending: pending.length,
            revoked: revoked.length,
        };
    }, [users, pending]);

    const roles = useMemo(() => {
        const counts = {};
        users.forEach((item) => (item.roles || []).forEach((role) => { counts[role] = (counts[role] || 0) + 1; }));
        return Object.entries(counts).sort((a, b) => b[1] - a[1]);
    }, [users]);

    if (loading) return <div className="deal-dashboard"><LoadingState message="Loading administration dashboard…" /></div>;
    if (error) return <div className="deal-dashboard"><ErrorState title="Administration data unavailable" message={error} onRetry={load} /></div>;

    return (
        <DashboardShell user={user} role={ROLES.ADMIN} description="Administrative access, user status and platform coverage." onRefresh={load}>
            <DashboardKpiRow items={[
                { label: "Total Users", value: stats.total, description: "Registered accounts", icon: Users },
                { label: "Active Users", value: stats.active, description: "Approved and enabled", icon: Target },
                { label: "Pending Approvals", value: stats.pending, description: "Awaiting review", icon: Clock3 },
                { label: "Revoked Access", value: stats.revoked, description: "Currently blocked", icon: AlertTriangle },
            ]} />

            <div className="dashboard-admin-grid">
                <Card>
                    <div className="dashboard-card-header"><div><h2>Access Overview</h2><p>Current user coverage by assigned platform role.</p></div></div>
                    {roles.length ? <div className="dashboard-admin-role-list">{roles.map(([role, count]) => <div className="dashboard-admin-role-row" key={role}><span>{role}</span><strong>{count}</strong></div>)}</div> : <EmptyState message="No role assignments are available." />}
                </Card>
                <Card>
                    <div className="dashboard-card-header"><div><h2>Pending Approvals</h2><p>Users waiting for administrator review.</p></div></div>
                    {pending.length ? <div className="dashboard-admin-pending-list">{pending.slice(0, 6).map((item) => <div className="dashboard-admin-user-row" key={item.user_id}><span className="dashboard-team-avatar">{String(item.full_name || "U").split(/\s+/).map((x) => x[0]).slice(0, 2).join("").toUpperCase()}</span><span className="dashboard-row-main"><strong>{item.full_name}</strong><small>{item.email}</small></span><span className="dashboard-admin-status">Pending</span></div>)}</div> : <EmptyState message="No pending approvals." />}
                </Card>
            </div>

            <Card>
                <div className="dashboard-card-header"><div><h2>Recent Users</h2><p>Latest registered accounts available to the administrator.</p></div></div>
                {users.length ? <div className="dashboard-admin-user-list">{users.slice(0, 6).map((item) => <div className="dashboard-admin-user-row" key={item.user_id}><span className="dashboard-team-avatar">{String(item.full_name || "U").split(/\s+/).map((x) => x[0]).slice(0, 2).join("").toUpperCase()}</span><span className="dashboard-row-main"><strong>{item.full_name}</strong><small>{item.email}</small></span><span className="dashboard-admin-user-role">{(item.roles || []).slice(0, 2).join(" · ") || "No role assigned"}</span><span className="dashboard-admin-status">{String(item.status || "Unknown").replace(/_/g, " ")}</span></div>)}</div> : <EmptyState message="No users found." />}
            </Card>
        </DashboardShell>
    );
}

export default function Dashboard() {
    const { user, activeRole, loading: authLoading } = useAuth();

    if (authLoading) return <div className="deal-dashboard"><LoadingState message="Loading dashboard…" /></div>;
    if (!activeRole) return <Navigate replace to="/unauthorized" />;
    if (activeRole === ROLES.ADMIN) return <AdminDashboard />;
    return <BusinessDashboard user={user} role={activeRole} />;
}
