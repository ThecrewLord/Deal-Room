import DashboardSkeleton from "../DashboardSkeleton";

import WelcomeSection from "../sections/WelcomeSection";
import OverviewCard from "../sections/OverviewCard";
import PipelineSummary from "../sections/PipelineSummary";
import QuickActions from "../sections/QuickActions";

import Deliverables from "../sections/Deliverables";
import PendingInputs from "../sections/PendingInputs";

const PresalesDashboard = ({ user, dashboard }) => {
    return (
        <DashboardSkeleton
            welcome={<WelcomeSection user={user} />}
            overview={<OverviewCard dashboard={dashboard} />}
            content={
                <div className="dashboard-grid">
                    <div className="dashboard-main">
                        <PipelineSummary dashboard={dashboard} />

                        <PendingInputs />
                    </div>

                    <aside className="dashboard-side">
                        <Deliverables />

                        <QuickActions />
                    </aside>
                </div>
            }
        />
    );
};

export default PresalesDashboard;