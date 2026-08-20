const DashboardSkeleton = ({
    welcome,
    overview,
    content,
}) => {
    return (
        <div className="dashboard-container">
            <div className="dashboard-header">
                {welcome}
            </div>

            <div className="dashboard-overview">
                {overview}
            </div>

            <div className="dashboard-content">
                {content}
            </div>
        </div>
    );
};

export default DashboardSkeleton;