const DashboardChart = ({
    title,
    children,
}) => {
    return (
        <section className="dashboard-section">
            <div className="dashboard-section-header">
                <h3>{title}</h3>
            </div>

            <div className="dashboard-chart">
                {children}
            </div>
        </section>
    );
};

export default DashboardChart;