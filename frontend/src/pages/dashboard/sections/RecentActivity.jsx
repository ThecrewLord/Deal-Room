import EmptyState from "./EmptyState";
import SectionCard from "./SectionCard";

const RecentActivity = () => {
    return (
        <SectionCard title="Recent Activity">
            <EmptyState
                title="No recent activity"
                subtitle="Recent opportunity updates will appear here."
            />
        </SectionCard>
    );
};

export default RecentActivity;