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
} from "lucide-react";

import {
    ResponsiveContainer,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";

import { useNavigate } from "react-router-dom";

const BLUE = "#2563EB";
const GREEN = "#16A34A";
const PURPLE = "#7C3AED";
const CYAN = "#0891B2";
const ORANGE = "#EA580C";
const SLATE = "#64748B";
const RED = "#DC2626";

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
                            `${color}12`,
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

export default function FigmaDashboard({
    dashboard,
    user,
}) {
    const navigate = useNavigate();

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

    const stageData =
        pipeline.map((item) => ({
            stage: item.stage,
            deals: item.count,
        }));

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
                    <h1>
                        Good morning,{" "}
                        {firstName} 👋
                    </h1>

                    <p>
                        Here is your pipeline
                        summary for{" "}
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
            </div>

            {/* =====================================================
                KPI ROW 1
            ====================================================== */}

            <div className="figma-kpi-grid">

                <KPICard
                    title="Total Opportunities"
                    value={
                        totalOpportunities
                    }
                    change={
                        `${dashboard?.open_opportunities ?? 0} currently open`
                    }
                    changeType="neutral"
                    icon={
                        <Target size={18} />
                    }
                    color={BLUE}
                />

                <KPICard
                    title="Pipeline Value"
                    value={fmt(pipelineValue)}
                    change={
                        `${dashboard?.open_opportunities ?? 0} open opportunities`
                    }
                    changeType="up"
                    icon={
                        <DollarSign size={18} />
                    }
                    color={GREEN}
                />

                <KPICard
                    title="Weighted Forecast"
                    value={
                        fmt(
                            weightedForecast
                        )
                    }
                    change="Probability-adjusted"
                    changeType="neutral"
                    icon={
                        <TrendingUp size={18} />
                    }
                    color={PURPLE}
                />

                <KPICard
                    title="Conversion Rate"
                    value={`${conversionRate}%`}
                    change={
                        `${closedWon} won / ${totalClosed} closed`
                    }
                    changeType={
                        conversionRate > 0
                            ? "up"
                            : "neutral"
                    }
                    icon={
                        <Percent size={18} />
                    }
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
                    icon={
                        <FlaskConical
                            size={18}
                        />
                    }
                    color={ORANGE}
                />

                <KPICard
                    title="Stage Ageing (Avg)"
                    value={`${averageAge} days`}
                    change="Average opportunity age"
                    changeType="neutral"
                    icon={
                        <Clock size={18} />
                    }
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
                        stalledDeals > 0
                            ? "down"
                            : "up"
                    }
                    icon={
                        <AlertTriangle
                            size={18}
                        />
                    }
                    color="#D97706"
                />

                <KPICard
                    title="Partner Contribution"
                    value={
                        partnerContribution
                    }
                    change="Partner-linked opportunities"
                    changeType="neutral"
                    icon={
                        <Handshake
                            size={18}
                        />
                    }
                    color="#0F766E"
                />

            </div>

            {/* =====================================================
                CHART ROW
            ====================================================== */}

            <div className="figma-dashboard-grid dashboard-grid-top">

                {/* Stage Distribution */}
                <Card>

                    <div className="figma-card-header">
                        <div>
                            <h3>
                                Stage Distribution
                            </h3>

                            <p>
                                Deals per pipeline
                                stage
                            </p>
                        </div>
                    </div>

                    {stageData.length > 0 ? (
                        <ResponsiveContainer
                            width="100%"
                            height={250}
                        >
                            <BarChart
                                data={stageData}
                                layout="vertical"
                                margin={{
                                    left: 0,
                                    right: 12,
                                }}
                            >
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                    stroke="#F1F5F9"
                                    horizontal={false}
                                />

                                <XAxis
                                    type="number"
                                    tick={{
                                        fontSize: 10,
                                        fill: "#94A3B8",
                                    }}
                                    axisLine={false}
                                    tickLine={false}
                                />

                                <YAxis
                                    type="category"
                                    dataKey="stage"
                                    tick={{
                                        fontSize: 10,
                                        fill: "#64748B",
                                    }}
                                    axisLine={false}
                                    tickLine={false}
                                    width={85}
                                />

                                <Tooltip />

                                <Bar
                                    dataKey="deals"
                                    fill={BLUE}
                                    radius={[
                                        0,
                                        4,
                                        4,
                                        0,
                                    ]}
                                    barSize={14}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <DashboardEmpty
                            title="No stage data"
                            subtitle="Pipeline stage data will appear here."
                        />
                    )}

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
                                "#2563EB",
                                "#3B82F6",
                                "#60A5FA",
                                "#7C3AED",
                                "#A78BFA",
                                "#0891B2",
                                "#0F766E",
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

            <div className="figma-dashboard-grid recent-grid">

                <Card className="recent-opportunities">

                    <div className="figma-card-header clickable-header">

                        <h3>
                            Recent Opportunities
                        </h3>

                        <button
                            onClick={() =>
                                navigate(
                                    "/opportunities"
                                )
                            }
                        >
                            View all
                            <ArrowRight
                                size={12}
                            />
                        </button>

                    </div>

                    {recentOpportunities.length >
                    0 ? (
                        <div className="dashboard-list">

                            {recentOpportunities.map(
                                (opportunity) => (
                                    <button
                                        key={
                                            opportunity.id
                                        }
                                        className="opportunity-row"
                                        onClick={() =>
                                            navigate(
                                                `/opportunities/${opportunity.id}`
                                            )
                                        }
                                    >
                                        <div className="opportunity-main">

                                            <strong>
                                                {
                                                    opportunity.name
                                                }
                                            </strong>

                                            <span>
                                                {
                                                    opportunity.account
                                                }{" "}
                                                ·{" "}
                                                {
                                                    opportunity.stage
                                                }
                                            </span>

                                        </div>

                                        <div className="opportunity-value">

                                            <strong>
                                                {fmt(
                                                    opportunity.value
                                                )}
                                            </strong>

                                            <span>
                                                {
                                                    opportunity.probability
                                                }
                                                % prob.
                                            </span>

                                        </div>

                                        <Badge
                                            status={
                                                opportunity.status
                                            }
                                        />
                                    </button>
                                )
                            )}

                        </div>
                    ) : (
                        <DashboardEmpty
                            title="No opportunities"
                            subtitle="Recent opportunities will appear here."
                        />
                    )}

                </Card>

                {/* Activity */}

                <Card>

                    <div className="figma-card-header">
                        <h3>
                            Recent Activity
                        </h3>
                    </div>

                    {recentActivity.length >
                    0 ? (
                        <div className="activity-list">

                            {recentActivity.map(
                                (activity) => {
                                    const Icon =
                                        getActivityIcon(
                                            activity.action
                                        );

                                    const color =
                                        getActivityColor(
                                            activity.action
                                        );

                                    return (
                                        <div
                                            key={
                                                activity.id
                                            }
                                            className="activity-row"
                                        >
                                            <div
                                                className="activity-icon"
                                                style={{
                                                    background:
                                                        `${color}15`,
                                                    color,
                                                }}
                                            >
                                                <Icon
                                                    size={
                                                        13
                                                    }
                                                />
                                            </div>

                                            <div>
                                                <p>
                                                    {
                                                        activity.details
                                                    }
                                                </p>

                                                <span>
                                                    {
                                                        activity.user
                                                    }{" "}
                                                    ·{" "}
                                                    {formatDate(
                                                        activity.timestamp
                                                    )}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                }
                            )}

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
                                "/poc"
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