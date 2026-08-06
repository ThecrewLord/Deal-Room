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

    return (
        <div className="dashboard-panel">
            <div className="panel-header">
                <h2>Pipeline Summary</h2>
            </div>

            <div className="summary-grid">
                {items.map((item) => (
                    <div
                        className="summary-item"
                        key={item.label}
                    >
                        <span>{item.label}</span>
                        <strong>{item.value ?? "-"}</strong>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PipelineSummary;