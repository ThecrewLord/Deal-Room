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
                    className="overview-card"
                    key={card.key}
                >

                    <p>{card.title}</p>

                    <h2>
                        {dashboard?.[card.key]}
                        {card.suffix || ""}
                    </h2>

                </div>

            ))}

        </section>

    );
};

export default OverviewCards;