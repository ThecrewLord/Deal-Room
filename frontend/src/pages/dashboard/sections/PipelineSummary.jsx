import {
    ResponsiveContainer,
    BarChart,
    CartesianGrid,
    XAxis,
    YAxis,
    Tooltip,
    Bar,
} from "recharts";

const PipelineSummary = ({ dashboard }) => {
    const items = [
        {
            label: "Pipeline Value",
            value: dashboard?.total_pipeline_value,
        },
        {
            label: "Weighted Forecast",
            value: dashboard?.weighted_forecast,
        },
        {
            label: "Win / Loss Ratio",
            value: dashboard?.win_loss_ratio,
        },
        {
            label: "Conversion Rate",
            value: `${dashboard?.conversion_rate ?? "-"}%`,
        },
        {
            label: "Stage Ageing",
            value: dashboard?.stage_ageing,
        },
        {
            label: "Stalled Deals",
            value: dashboard?.stalled_deals,
        },
    ];

    // Uses backend data if available.
    // Empty array keeps the component safe until the API is updated.
    const chartData = dashboard?.pipeline_by_stage ?? [];

    return (
        <div className="dashboard-panel">
            <div className="panel-header">
                <h2>Pipeline Summary</h2>
            </div>

            <div className="pipeline-grid">
                {items.map((item) => (
                    <div
                        key={item.label}
                        className="pipeline-card"
                    >
                        <span>{item.label}</span>

                        <h3>{item.value ?? "-"}</h3>
                    </div>
                ))}
            </div>

            {chartData.length > 0 && (
                <div className="pipeline-chart">
                    <ResponsiveContainer
                        width="100%"
                        height={280}
                    >
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />

                            <XAxis dataKey="stage" />

                            <YAxis />

                            <Tooltip />

                            <Bar
                                dataKey="count"
                                radius={[6, 6, 0, 0]}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
};

export default PipelineSummary;