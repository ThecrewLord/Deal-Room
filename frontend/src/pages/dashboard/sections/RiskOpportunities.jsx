import SectionCard from "./SectionCard";
import EmptyState from "./EmptyState";

const RiskOpportunities = ({ dashboard }) => {
    if (!dashboard?.risk_opportunities?.length) {
        return (
            <SectionCard title="Risk Opportunities">
                <EmptyState
                    title="No at-risk opportunities"
                    subtitle="Everything looks healthy."
                />
            </SectionCard>
        );
    }

    return (
        <SectionCard title="Risk Opportunities">
            <ul className="dashboard-list">
                {dashboard.risk_opportunities.map((item) => (
                    <li key={item.id}>
                        <strong>{item.name}</strong>
                    </li>
                ))}
            </ul>
        </SectionCard>
    );
};

export default RiskOpportunities;