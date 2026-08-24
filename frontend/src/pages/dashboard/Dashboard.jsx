import {
    Target,
    DollarSign,
    TrendingUp,
    Percent,
    FlaskConical,
    Clock,
    AlertTriangle,
    Handshake,
    ArrowRight,
    CheckCircle,
    XCircle,
    Circle,
    BriefcaseBusiness,
    Activity,
    CalendarDays,
} from "lucide-react";

import {
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Tooltip,
} from "recharts";

import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { getDashboardSummary } from "../../api/dashboardApi";
import Phase5RolePanel from "./sections/Phase5RolePanel";
import QuickActions from "./sections/QuickActions";
import { ROLES } from "../../auth/roles";
import { useAuth } from "../../context/AuthContext";

const BLUE = "var(--color-primary)";
const GREEN = "var(--color-success)";
const PURPLE = "var(--color-chart-purple)";
const CYAN = "var(--color-info)";
const ORANGE = "var(--color-chart-orange)";
const SLATE = "var(--color-text-secondary)";
const RED = "var(--color-danger)";

const fmt = (value) => {
    const number = Number(value || 0);

    if (number >= 1000000) {
        return `$${(
            number / 1000000
        ).toFixed(1)}M`;
    }

    if (number >= 1000) {
        return `$${(
            number / 1000
        ).toFixed(0)}K`;
    }

    return `$${number.toLocaleString()}`;
};

const formatDate = (value) => {
    if (!value) {
        return "-";
    }

    return new Date(value).toLocaleDateString(
        undefined,
        {
            day: "numeric",
            month: "short",
            year: "numeric",
        }
    );
};

const getActivityIcon = (action) => {
    const normalized =
        String(action || "").toUpperCase();

    if (normalized.includes("CREATE")) {
        return CheckCircle;
    }

    if (normalized.includes("DELETE")) {
        return XCircle;
    }

    if (normalized.includes("UPDATE")) {
        return TrendingUp;
    }

    return Circle;
};

const getActivityColor = (action) => {
    const normalized =
        String(action || "").toUpperCase();

    if (normalized.includes("CREATE")) {
        return GREEN;
    }

    if (normalized.includes("DELETE")) {
        return RED;
    }

    if (normalized.includes("UPDATE")) {
        return BLUE;
    }

    return SLATE;
};

function Card({
    children,
    className = "",
}) {
    return (
        <section
            className={`figma-card ${className}`}
        >
            {children}
        </section>
    );
}

function Badge({ status }) {
    const normalized =
        String(status || "Unknown");

    const styles = {
        Open: "badge-open",
        Won: "badge-won",
        Lost: "badge-lost",
        Stalled: "badge-stalled",
        Active: "badge-open",
        Completed: "badge-won",
        Upcoming: "badge-upcoming",
        Failed: "badge-lost",
        Planned: "badge-upcoming",
    };

    return (
        <span
            className={`dashboard-badge ${
                styles[normalized] ||
                "badge-upcoming"
            }`}
        >
            {normalized}
        </span>
    );
}

function KPICard({
    title,
    value,
    change,
    changeType = "neutral",
    icon,
    color,
}) {
    return (
        <div className="figma-kpi-card">
            <div className="kpi-top">
                <span className="kpi-title">
                    {title}
                </span>

                <span
                    className="kpi-icon"
                    style={{
                        color,
                        background:
                            `color-mix(in srgb, ${color} 8%, transparent)`,
                    }}
                >
                    {icon}
                </span>
            </div>

            <strong className="kpi-value">
                {value}
            </strong>

            <span
                className={`kpi-change ${changeType}`}
            >
                {change}
            </span>
        </div>
    );
}

export default function Dashboard() {
    const navigate = useNavigate();
    const { user, activeRole, loading: authLoading } = useAuth();

    const [dashboard, setDashboard] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let mounted = true;

        const loadDashboard = async () => {
            try {
                setLoading(true);
                setError("");
                const response = await getDashboardSummary();
                if (mounted) {
                    setDashboard(response);
                }
            } catch (err) {
                if (mounted) {
                    setError(
                        err?.response?.data?.message ||
                        "Unable to load dashboard."
                    );
                }
            } finally {
                if (mounted) {
                    setLoading(false);
                }
            }
        };

        if (!authLoading && activeRole) {
            loadDashboard();
        }

        return () => {
            mounted = false;
        };
    }, [authLoading, activeRole]);

    if (authLoading || loading) {
        return <DashboardLoading />;
    }

    if (error) {
        return <DashboardError message={error} onRetry={() => window.location.reload()} />;
    }

    if (!activeRole || activeRole === ROLES.ADMIN) {
        return (
            <Navigate
                replace
                to={activeRole === ROLES.ADMIN ? "/admin/approval" : "/unauthorized"}
            />
        );
    }

    const totalOpportunities =
        dashboard?.total_opportunities ?? 0;

    const pipelineValue =
        dashboard?.total_pipeline_value ?? 0;

    const weightedForecast =
        dashboard?.weighted_forecast ?? 0;

    const conversionRate =
        dashboard?.conversion_rate ?? 0;

    const activePOCs =
        dashboard?.active_pocs ?? 0;

    const averageAge =
        dashboard?.average_stage_ageing ?? 0;

    const stalledDeals =
        dashboard?.stalled_deals ?? 0;

    const partnerContribution =
        dashboard?.partner_contribution ?? 0;

    const pipeline =
        dashboard?.pipeline_by_stage || [];

    const recentOpportunities =
        dashboard?.recent_opportunities || [];

    const recentActivity =
        dashboard?.recent_activity || [];

    const upcomingPOCs =
        dashboard?.upcoming_pocs || [];

    const closedWon =
        dashboard?.closed_won ?? 0;

    const closedLost =
        dashboard?.closed_lost ?? 0;

    const openOpportunities =
        dashboard?.open_opportunities ?? 0;

    const totalClosed =
        closedWon + closedLost;

    const winLossData = [
        {
            name: "Won",
            value:
                totalClosed > 0
                    ? Math.round(
                        (
                            closedWon /
                            totalClosed
                        ) * 100
                    )
                    : 0,
            color: GREEN,
        },
        {
            name: "Lost",
            value:
                totalClosed > 0
                    ? Math.round(
                        (
                            closedLost /
                            totalClosed
                        ) * 100
                    )
                    : 0,
            color: RED,
        },
        {
            name: "In Progress",
            value:
                totalOpportunities > 0
                    ? Math.round(
                        (
                            openOpportunities /
                            totalOpportunities
                        ) * 100
                    )
                    : 0,
            color: BLUE,
        },
    ];

    const maxPipelineValue = Math.max(
        ...pipeline.map(
            (item) =>
                Number(item.value || 0)
        ),
        1
    );

    const firstName =
        user?.full_name
            ?.trim()
            ?.split(/\s+/)[0] ||
        "there";

    return (
        <div className="figma-dashboard fade-in">

            {/* =====================================================
                WELCOME
            ====================================================== */}

            <div className="figma-dashboard-welcome">
    <div>
        <span className="dashboard-eyebrow">
            SALES INTELLIGENCE
        </span>

        <h1>
            Good morning, {firstName} 👋
        </h1>

        <p>
            Here is your pipeline summary for{" "}
            {new Date().toLocaleDateString(
                undefined,
                {
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                }
            )}
        </p>
    </div>

    <span className="dashboard-role-badge">
        {activeRole || "No Active Role"}
    </span>
</div>


{/* =====================================================
    KPI ROW 1
====================================================== */}

<div className="figma-kpi-grid">

    <KPICard
        title="Total Opportunities"
        value={totalOpportunities}
        change={
            `${dashboard?.open_opportunities ?? 0} currently open`
        }
        changeType="neutral"
        icon={<Target size={18} />}
        color={BLUE}
    />

    <KPICard
        title="Pipeline Value"
        value={fmt(pipelineValue)}
        change={
            `${dashboard?.open_opportunities ?? 0} open opportunities`
        }
        changeType="up"
        icon={<DollarSign size={18} />}
        color={GREEN}
    />

    <KPICard
        title="Weighted Forecast"
        value={fmt(weightedForecast)}
        change="Probability-adjusted"
        changeType="neutral"
        icon={<TrendingUp size={18} />}
        color={PURPLE}
    />

    <KPICard
        title="Conversion Rate"
        value={`${conversionRate}%`}
        change={`${closedWon} won / ${totalClosed} closed`}
        changeType={
            conversionRate > 0 ? "up" : "neutral"
        }
        icon={<Percent size={18} />}
        color={CYAN}
    />

</div>


{/* =====================================================
    KPI ROW 2
====================================================== */}

<div className="figma-kpi-grid">

    <KPICard
        title="Active POCs"
        value={activePOCs}
        change={
            upcomingPOCs.length
                ? `${upcomingPOCs.length} upcoming`
                : "No upcoming POCs"
        }
        changeType="neutral"
        icon={<FlaskConical size={18} />}
        color={ORANGE}
    />

    <KPICard
        title="Stage Ageing (Avg)"
        value={`${averageAge} days`}
        change="Average opportunity age"
        changeType="neutral"
        icon={<Clock size={18} />}
        color={SLATE}
    />

    <KPICard
        title="Stalled Deals"
        value={stalledDeals}
        change={
            stalledDeals > 0
                ? "Needs attention"
                : "No stalled deals"
        }
        changeType={
            stalledDeals > 0 ? "down" : "up"
        }
        icon={<AlertTriangle size={18} />}
        color={ORANGE}
    />

    <KPICard
        title="Partner Contribution"
        value={partnerContribution}
        change="Partner-linked opportunities"
        changeType="neutral"
        icon={<Handshake size={18} />}
        color="var(--color-chart-teal)"
    />

</div>


{/* =====================================================
    ROLE-SPECIFIC WORK
====================================================== */}

{[
    ROLES.PRE_SALES_MANAGER,
    ROLES.SOLUTION_ENGINEER,
    ROLES.DELIVERY,
].includes(activeRole) && (
    <Phase5RolePanel />
)}


{/* =====================================================
    QUICK ACTIONS
====================================================== */}

<div className="dashboard-role-actions">
    <QuickActions />
</div>

            {/* =====================================================
                CHART ROW
            ====================================================== */}

            <div className="figma-dashboard-grid dashboard-grid-top">

                {/* Stage Distribution */}
                <Card className="stage-distribution-card">
                    <div className="figma-card-header">
                        <div>
                            <h3>Stage Distribution</h3>
                            <p>Deals across your sales pipeline by stage.</p>
                        </div>
                    </div>
                    <div className="pipeline-overview">
                        {pipeline.map((item, index) => {
                            const value = Number(item.value || 0);
                            const count = Number(item.count || 0);
                            const width = value > 0 ? Math.max((value / maxPipelineValue) * 100, 6) : 0;
                            return (
                                <div className="pipeline-stage-row" key={item.stage}>
                                    <div className="pipeline-stage-index">{index + 1}</div>
                                    <div className="pipeline-stage-main">
                                        <div className="pipeline-stage-head">
                                            <strong>{item.stage}</strong>
                                            <span>{count} {count === 1 ? "deal" : "deals"}</span>
                                        </div>
                                        <div className="pipeline-stage-track">
                                            <div className={`pipeline-stage-fill stage-fill-${Math.min(index + 1, 8)}`} style={{ width: `${width}%` }} />
                                        </div>
                                    </div>
                                    <div className="pipeline-stage-value">{fmt(value)}</div>
                                </div>
                            );
                        })}
                        {!pipeline.length && <div className="figma-dashboard-empty">No stage data available.</div>}
                    </div>
                </Card>

                {/* Win Loss */}
                <Card>

                    <div className="figma-card-header">
                        <div>
                            <h3>
                                Win vs Loss Ratio
                            </h3>

                            <p>
                                Current deal
                                outcomes
                            </p>
                        </div>
                    </div>

                    <ResponsiveContainer
                        width="100%"
                        height={170}
                    >
                        <PieChart>
                            <Pie
                                data={winLossData}
                                cx="50%"
                                cy="50%"
                                innerRadius={42}
                                outerRadius={65}
                                paddingAngle={3}
                                dataKey="value"
                            >
                                {winLossData.map(
                                    (
                                        entry
                                    ) => (
                                        <Cell
                                            key={
                                                entry.name
                                            }
                                            fill={
                                                entry.color
                                            }
                                        />
                                    )
                                )}
                            </Pie>

                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>

                    <div className="win-loss-list">

                        {winLossData.map(
                            (item) => (
                                <div
                                    key={
                                        item.name
                                    }
                                    className="win-loss-row"
                                >
                                    <span>
                                        <i
                                            style={{
                                                background:
                                                    item.color,
                                            }}
                                        />

                                        {
                                            item.name
                                        }
                                    </span>

                                    <strong>
                                        {
                                            item.value
                                        }%
                                    </strong>
                                </div>
                            )
                        )}

                    </div>

                </Card>

            </div>

            {/* =====================================================
                PIPELINE FUNNEL
            ====================================================== */}

            <Card className="pipeline-funnel-card">

                <div className="figma-card-header">
                    <div>
                        <h3>
                            Pipeline Funnel
                        </h3>

                        <p>
                            Deal volume and value
                            by stage
                        </p>
                    </div>
                </div>

                <div className="pipeline-funnel">

                    {pipeline.map(
                        (item, index) => {
                            const percentage =
                                (
                                    Number(
                                        item.value ||
                                        0
                                    ) /
                                    maxPipelineValue
                                ) * 100;

                            const colors = [
                                "var(--color-primary)",
                                "var(--color-chart-blue-light)",
                                "var(--color-chart-blue-soft)",
                                "var(--color-chart-purple)",
                                "var(--color-chart-purple-light)",
                                "var(--color-info)",
                                "var(--color-chart-teal)",
                            ];

                            return (
                                <div
                                    key={
                                        item.stage
                                    }
                                    className="pipeline-funnel-row"
                                >
                                    <span className="pipeline-stage">
                                        {
                                            item.stage
                                        }
                                    </span>

                                    <div className="pipeline-track">
                                        <div
                                            className="pipeline-fill"
                                            style={{
                                                width: `${Math.max(
                                                    percentage,
                                                    2
                                                )}%`,
                                                background:
                                                    colors[
                                                        index %
                                                        colors.length
                                                    ],
                                            }}
                                        >
                                            {percentage >
                                                20 && (
                                                <span>
                                                    {fmt(
                                                        item.value
                                                    )}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    <strong className="pipeline-count">
                                        {
                                            item.count
                                        }
                                    </strong>
                                </div>
                            );
                        }
                    )}

                </div>

            </Card>

            {/* =====================================================
                RECENT OPPORTUNITIES + ACTIVITY
            ====================================================== */}

            {/* =====================================================
  {/* =====================================================
    RECENT OPPORTUNITIES + ACTIVITY
====================================================== */}

<div className="dashboard-lower-grid">

    {/* =================================================
        RECENT OPPORTUNITIES
    ================================================== */}

    <Card className="recent-opportunities">

        <div className="dashboard-section-header">

            <div className="dashboard-section-title">

                <div className="section-icon section-icon-blue">
                    <BriefcaseBusiness size={17} />
                </div>

                <div>
                    <h3>Recent Opportunities</h3>

                    <p>
                        Latest deals added or updated in your pipeline.
                    </p>
                </div>

            </div>

            <button
                className="dashboard-view-all"
                onClick={() => navigate("/opportunities")}
            >
                View all
                <ArrowRight size={13} />
            </button>

        </div>


        {recentOpportunities.length > 0 ? (

            <div className="recent-opportunity-grid">

                {recentOpportunities
                    .slice(0, 5)
                    .map((opportunity, index) => {

                        const accents = [
                            "blue",
                            "green",
                            "purple",
                            "orange",
                            "cyan",
                        ];

                        const accent =
                            accents[index % accents.length];

                        const name =
                            opportunity.name || "Opportunity";

                        const initial =
                            name
                                .trim()
                                .charAt(0)
                                .toUpperCase();

                        return (
                            <button
                                key={opportunity.id}
                                className={`modern-opportunity-card accent-${accent}`}
                                onClick={() =>
                                    navigate(
                                        `/opportunities/${opportunity.id}`
                                    )
                                }
                            >

                                {/* TOP */}
                                <div className="modern-opportunity-top">

                                    <div
                                        className={`opportunity-avatar avatar-${accent}`}
                                    >
                                        {initial}
                                    </div>

                                    <div className="modern-opportunity-info">

                                        <strong>
                                            {name}
                                        </strong>

                                        <span>
                                            {opportunity.account ||
                                                "Account"}
                                        </span>

                                        <small>
                                            {opportunity.stage ||
                                                "Stage"}
                                        </small>

                                    </div>

                                    <Badge
                                        status={
                                            opportunity.status
                                        }
                                    />

                                </div>


                                {/* BOTTOM */}
                                <div className="modern-opportunity-bottom">

                                    <strong>
                                        {fmt(
                                            opportunity.value
                                        )}
                                    </strong>

                                    <span>
                                        {opportunity.probability ?? 0}
                                        % probability
                                    </span>

                                </div>

                            </button>
                        );
                    })}

            </div>

        ) : (

            <DashboardEmpty
                title="No opportunities"
                subtitle="Recent opportunities will appear here."
            />

        )}

    </Card>


    {/* =================================================
        RECENT ACTIVITY
    ================================================== */}

    <Card className="recent-activity-card">

        <div className="dashboard-section-header">

            <div className="dashboard-section-title">

                <div className="section-icon section-icon-purple">
                    <Activity size={17} />
                </div>

                <div>
                    <h3>Recent Activity</h3>

                    <p>
                        Latest actions across your Deal Room.
                    </p>
                </div>

            </div>

        </div>


        {recentActivity.length > 0 ? (

            <div className="modern-activity-list">

                {recentActivity
                    .slice(0, 6)
                    .map((activity, index) => {

                        const Icon =
                            getActivityIcon(
                                activity.action
                            );

                        const color =
                            getActivityColor(
                                activity.action
                            );

                        const activityColors = [
                            "green",
                            "purple",
                            "orange",
                            "blue",
                            "green",
                            "purple",
                        ];

                        const accent =
                            activityColors[
                                index %
                                activityColors.length
                            ];

                        return (
                            <div
                                key={activity.id}
                                className="modern-activity-row"
                            >

                                {/* TIMELINE */}
                                <div className="activity-timeline">

                                    <div
                                        className={`activity-avatar activity-avatar-${accent}`}
                                    >
                                        <Icon size={15} />
                                    </div>

                                    {index <
                                        Math.min(
                                            recentActivity.length,
                                            6
                                        ) -
                                            1 && (
                                        <span className="activity-line" />
                                    )}

                                </div>


                                {/* CONTENT */}
                                <div className="activity-content">

                                    <p>
                                        {activity.details}
                                    </p>

                                    <div className="activity-meta">

                                        <span>
                                            {activity.user}
                                        </span>

                                        <span className="activity-date">
                                            <CalendarDays
                                                size={12}
                                            />

                                            {formatDate(
                                                activity.timestamp
                                            )}
                                        </span>

                                    </div>

                                </div>

                            </div>
                        );
                    })}

            </div>

        ) : (

            <DashboardEmpty
                title="No recent activity"
                subtitle="System activity will appear here."
            />

        )}

    </Card>

</div>

            {/* =====================================================
                UPCOMING POCS
            ====================================================== */}

            <Card className="upcoming-pocs">

                <div className="figma-card-header clickable-header">

                    <h3>
                        Upcoming POCs
                    </h3>

                    <button
                        onClick={() =>
                            navigate(
                                "/pocs"
                            )
                        }
                    >
                        View all
                        <ArrowRight
                            size={12}
                        />
                    </button>

                </div>

                {upcomingPOCs.length > 0 ? (
                    <div className="dashboard-list">

                        {upcomingPOCs.map(
                            (poc) => (
                                <div
                                    key={poc.id}
                                    className="poc-row"
                                >
                                    <div>
                                        <strong>
                                            {
                                                poc.opportunity
                                            }
                                        </strong>

                                        <span>
                                            {
                                                poc.objective
                                            }
                                        </span>
                                    </div>

                                    <div className="poc-meta">
                                        <span>
                                            {formatDate(
                                                poc.target_date
                                            )}
                                        </span>

                                        <small>
                                            {
                                                poc.stakeholder_signoff
                                            }
                                        </small>
                                    </div>

                                    <Badge
                                        status={
                                            poc.status
                                        }
                                    />
                                </div>
                            )
                        )}

                    </div>
                ) : (
                    <DashboardEmpty
                        title="No upcoming POCs"
                        subtitle="Scheduled proof-of-concepts will appear here."
                    />
                )}

            </Card>

        </div>
    );
}

function DashboardEmpty({
    title,
    subtitle,
}) {
    return (
        <div className="figma-dashboard-empty">
            <strong>{title}</strong>
            <span>{subtitle}</span>
        </div>
    );
}

function DashboardLoading() {
    return (
        <div className="figma-dashboard-loading">
            <div className="dashboard-loading-title" />
            <div className="dashboard-loading-grid">
                {Array.from({ length: 8 }).map((_, index) => (
                    <div key={index} className="dashboard-loading-card" />
                ))}
            </div>
            <div className="dashboard-loading-large" />
        </div>
    );
}

function DashboardError({ message, onRetry }) {
    return (
        <div className="figma-dashboard-error">
            <div>
                <h2>Unable to load dashboard</h2>
                <p>{message}</p>
                <button onClick={onRetry}>Retry</button>
            </div>
        </div>
    );
}
