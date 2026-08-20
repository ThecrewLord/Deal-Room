import EmptyState from "./EmptyState";
import SectionCard from "./SectionCard";

const Deliverables = () => {
    return (
        <SectionCard title="My Deliverables">
            <EmptyState
                title="No pending deliverables"
                subtitle="Assigned deliverables will appear here."
            />
        </SectionCard>
    );
};

export default Deliverables;