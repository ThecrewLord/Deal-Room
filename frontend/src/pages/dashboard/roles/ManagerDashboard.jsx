import DashboardSkeleton from "../DashboardSkeleton";

import WelcomeSection from "../sections/WelcomeSection";
import OverviewCard from "../sections/OverviewCard";
import PipelineSummary from "../sections/PipelineSummary";
import TeamPerformance from "../sections/TeamPerformance";
import RiskOpportunities from "../sections/RiskOpportunities";
import QuickActions from "../sections/QuickActions";

const ManagerDashboard = ({ user, dashboard }) => {
    return (
        <DashboardSkeleton
            welcome={<WelcomeSection user={user} />}
            overview={<OverviewCard dashboard={dashboard} />}
            content={
                <div className="dashboard-grid">
                    <div className="dashboard-main">
                        <PipelineSummary dashboard={dashboard} />

                        <TeamPerformance dashboard={dashboard} />
                    </div>

                    <aside className="dashboard-side">
                        <RiskOpportunities dashboard={dashboard} />

                        <QuickActions />
                    </aside>
                </div>
            }
        />
    );
};

export default ManagerDashboard;