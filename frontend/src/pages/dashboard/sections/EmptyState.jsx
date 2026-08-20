const EmptyState = ({
    title = "Nothing to show",
    subtitle = "There is currently no data available.",
}) => {
    return (
        <div className="dashboard-empty">
            <div className="dashboard-empty-icon">
                📄
            </div>

            <h3>{title}</h3>

            <p>{subtitle}</p>
        </div>
    );
};

export default EmptyState;