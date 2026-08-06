const DashboardSkeleton = ({
    welcome,
    overview,
    content,
}) => {
    return (
        <div className="dashboard-page">

            {welcome}

            {overview}

            {content}

        </div>
    );
};

export default DashboardSkeleton; 