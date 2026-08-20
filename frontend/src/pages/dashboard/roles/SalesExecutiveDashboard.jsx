import DashboardSkeleton from "../DashboardSkeleton";

import WelcomeSection from "../sections/WelcomeSection";
import OverviewCards from "../sections/OverviewCard";
import PipelineSummary from "../sections/PipelineSummary";
import QuickActions from "../sections/QuickActions";
import RecentActivity from "../sections/RecentActivity";

const SalesExecutiveDashboard = ({ user, dashboard }) => {
    return (
        <DashboardSkeleton
            welcome={<WelcomeSection user={user} />}
            overview={<OverviewCards dashboard={dashboard} />}
            content={
                <div className="dashboard-grid">
                    <div className="dashboard-main">
                        <PipelineSummary dashboard={dashboard} />

                        <RecentActivity />
                    </div>

                    <aside className="dashboard-side">
                        <QuickActions />
                    </aside>
                </div>
            }
        />
    );
};

export default SalesExecutiveDashboard;