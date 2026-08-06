import DashboardSkeleton from "../DashboardSkeleton";

import WelcomeSection from "../sections/WelcomeSection";
import OverviewCards from "../sections/OverviewCard";
import PipelineSummary from "../sections/PipelineSummary";
import QuickActions from "../sections/QuickActions";
import RecentActivity from "../sections/RecentActivity";

const SalesExecutiveDashboard = ({ user, dashboard }) => {
    return (
        <DashboardSkeleton
            welcome={
                <WelcomeSection user={user} />
            }
            overview={
                <OverviewCards dashboard={dashboard} />
            }
            content={
                <>
                    <section className="dashboard-content">
                        <PipelineSummary dashboard={dashboard} />
                        <QuickActions />
                    </section>

                    <RecentActivity />
                </>
            }
        />
    );
};

export default SalesExecutiveDashboard;