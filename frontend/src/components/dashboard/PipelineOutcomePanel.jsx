import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import Card from "../ui/Card";
import EmptyState from "../ui/EmptyState";

const COLORS = ["var(--color-success)", "var(--color-danger)"];
const STAGE_COLORS = [
    "var(--color-primary)",
    "var(--color-chart-blue-light)",
    "var(--color-info)",
    "var(--color-chart-purple)",
    "var(--color-chart-orange)",
    "var(--color-warning)",
    "var(--color-success)",
    "var(--color-danger)",
];

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

export default function PipelineOutcomePanel({ pipeline = [], won = 0, lost = 0, open = 0 }) {
    const wonCount = Number(won || 0);
    const lostCount = Number(lost || 0);
    const openCount = Number(open || 0);
    const closed = wonCount + lostCount;
    const winPct = closed ? Math.round((wonCount / closed) * 100) : 0;
    const lossPct = closed ? Math.round((lostCount / closed) * 100) : 0;
    const maxPipeline = Math.max(...pipeline.map((item) => Number(item.value || 0)), 1);
    const outcomeData = [
        { name: "Won", value: wonCount },
        { name: "Lost", value: lostCount },
    ].filter((item) => item.value > 0);

    return (
        <div className="dashboard-pipeline-outcome-grid">
            <Card className="dashboard-chart-card">
                <div className="dashboard-card-header">
                    <div>
                        <h2>Pipeline Funnel</h2>
                        <p>Opportunity count and value by stage.</p>
                    </div>
                </div>
                {pipeline.length ? (
                    <div className="dashboard-funnel">
                        {pipeline.map((item, index) => {
                            const value = Number(item.value || 0);
                            const width = value ? Math.max((value / maxPipeline) * 100, 8) : 0;
                            return (
                                <div className="dashboard-funnel-row" key={item.stage}>
                                    <div className="dashboard-funnel-label" title={item.stage}>{item.stage}</div>
                                    <div className="dashboard-funnel-track">
                                        <div
                                            className="dashboard-funnel-fill"
                                            style={{
                                                width: `${width}%`,
                                                background: STAGE_COLORS[index % STAGE_COLORS.length],
                                            }}
                                        >
                                            {width >= 24 && <span>{money(value)}</span>}
                                        </div>
                                    </div>
                                    <strong>{item.count ?? 0}</strong>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <EmptyState message="No pipeline stage data available." />
                )}
            </Card>

            <Card className="dashboard-chart-card">
                <div className="dashboard-card-header">
                    <div>
                        <h2>Win vs Loss Ratio</h2>
                        <p>Closed outcomes, with open work shown separately.</p>
                    </div>
                </div>
                {outcomeData.length ? (
                    <>
                        <div className="dashboard-outcome-chart">
                            <ResponsiveContainer width="100%" height={190}>
                                <PieChart>
                                    <Pie
                                        data={outcomeData}
                                        dataKey="value"
                                        nameKey="name"
                                        innerRadius={52}
                                        outerRadius={76}
                                        paddingAngle={3}
                                    >
                                        {outcomeData.map((entry) => (
                                            <Cell key={entry.name} fill={COLORS[entry.name === "Won" ? 0 : 1]} />
                                        ))}
                                    </Pie>
                                    <Tooltip formatter={(value) => [`${value} deals`, ""]} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="dashboard-outcome-legend">
                            <span><i className="won" /> Won <b>{winPct}% of closed</b></span>
                            <span><i className="lost" /> Lost <b>{lossPct}% of closed</b></span>
                            <span><i className="progress" /> In Progress <b>{openCount} deals</b></span>
                        </div>
                    </>
                ) : (
                    <div className="dashboard-outcome-empty">
                        <EmptyState message="No closed outcomes yet." />
                        <span className="dashboard-outcome-open">In Progress: <strong>{openCount}</strong> deals</span>
                    </div>
                )}
            </Card>
        </div>
    );
}
