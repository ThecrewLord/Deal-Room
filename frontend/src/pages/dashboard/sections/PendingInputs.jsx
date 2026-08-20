import EmptyState from "./EmptyState";
import SectionCard from "./SectionCard";

const PendingInputs = () => {
    return (
        <SectionCard title="Pending Inputs">
            <EmptyState
                title="Nothing pending"
                subtitle="Items requiring your attention will appear here."
            />
        </SectionCard>
    );
};

export default PendingInputs;