const cards = [
    {
        key: "total_opportunities",
        title: "Total Opportunities",
    },
    {
        key: "open_opportunities",
        title: "Open Opportunities",
    },
    {
        key: "closed_won",
        title: "Closed Won",
    },
    {
        key: "closed_lost",
        title: "Closed Lost",
    },
    {
        key: "total_pipeline_value",
        title: "Pipeline Value",
    },
    {
        key: "weighted_forecast",
        title: "Weighted Forecast",
    },
    {
        key: "conversion_rate",
        title: "Conversion Rate",
        suffix: "%",
    },
    {
        key: "active_pocs",
        title: "Active POCs",
    },
];

const OverviewCards = ({ dashboard }) => {

    return (

        <section className="overview-grid">

            {cards.map((card) => (

                <div
                    key={card.title}
                    className="overview-card clickable-card"
                    onClick={() => navigate(card.route)}
                >
                    <div className="overview-card-header">
                        <span>{card.title}</span>

                        {card.icon && (
                            <div className="overview-icon">
                                {card.icon}
                            </div>
                        )}
                    </div>

                    <h2>{card.value ?? "-"}</h2>

                    {card.subtitle && (
                        <p className="overview-subtitle">
                            {card.subtitle}
                        </p>
                    )}
                </div>

            ))}

        </section>

    );
};

export default OverviewCards;