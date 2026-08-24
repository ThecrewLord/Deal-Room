import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import Card from "../../components/ui/Card";

const COLORS = ["var(--color-success)", "var(--color-danger)", "var(--color-primary)"];
const STAGE_COLORS = [
    "var(--color-primary)", "var(--color-chart-blue-light)", "var(--color-info)",
    "var(--color-chart-purple)", "var(--color-chart-orange)", "var(--color-warning)",
    "var(--color-success)", "var(--color-danger)",
];

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

export default function PipelineOutcomePanel({
    pipeline = [],
    won = 0,
    lost = 0,
    open = 0,
    total = 0,
}) {
    const closed = Number(won || 0) + Number(lost || 0);
    const winPct = closed ? Math.round((Number(won || 0) / closed) * 100) : 0;
    const lossPct = closed ? Math.round((Number(lost || 0) / closed) * 100) : 0;
    const inProgressPct = Number(total || 0) ? Math.round((Number(open || 0) / Number(total)) * 100) : 0;
    const donut = [
        { name: "Won", value: Number(won || 0) },
        { name: "Lost", value: Number(lost || 0) },
        { name: "In Progress", value: Number(open || 0) },
    ];
    const maxPipeline = Math.max(...pipeline.map((item) => Number(item.value || 0)), 1);

    return (
        <div className="pipeline-outcome-grid">
            <Card className="pipeline-outcome-card">
                <div className="pipeline-outcome-header">
                    <div><h2>Win vs Loss Ratio</h2><p>Current deal outcomes</p></div>
                </div>
                <div className="pipeline-donut-layout">
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie data={donut} dataKey="value" nameKey="name" innerRadius={52} outerRadius={76} paddingAngle={2}>
                                {donut.map((entry, index) => <Cell key={entry.name} fill={COLORS[index]} />)}
                            </Pie>
                            <Tooltip formatter={(value) => [`${value} deals`, ""]} />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="pipeline-donut-legend">
                        <span><i className="won" /> Won <b>{winPct}%</b></span>
                        <span><i className="lost" /> Lost <b>{lossPct}%</b></span>
                        <span><i className="progress" /> In Progress <b>{inProgressPct}%</b></span>
                    </div>
                </div>
            </Card>

            <Card className="pipeline-outcome-card">
                <div className="pipeline-outcome-header">
                    <div><h2>Pipeline Funnel</h2><p>Deal volume and value by stage</p></div>
                </div>
                <div className="pipeline-funnel compact">
                    {pipeline.map((item, index) => {
                        const value = Number(item.value || 0);
                        const width = value ? Math.max((value / maxPipeline) * 100, 8) : 0;
                        return (
                            <div className="pipeline-funnel-row" key={item.stage}>
                                <span className="pipeline-stage" title={item.stage}>{item.stage}</span>
                                <div className="pipeline-track">
                                    <div className="pipeline-fill" style={{ width: `${width}%`, background: STAGE_COLORS[index % STAGE_COLORS.length] }}>
                                        {width >= 20 && <span>{money(value)}</span>}
                                    </div>
                                </div>
                                <strong className="pipeline-count">{item.count ?? 0}</strong>
                            </div>
                        );
                    })}
                    {!pipeline.length && <div className="pipeline-empty">No pipeline stage data available.</div>}
                </div>
            </Card>
        </div>
    );
}
