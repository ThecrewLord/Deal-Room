import KpiCard from "../ui/KpiCard";

export default function DashboardKpiRow({ items = [] }) {
    return (
        <div className="dashboard-kpi-row">
            {items.map((item) => (
                <KpiCard
                    key={item.label}
                    icon={item.icon}
                    label={item.label}
                    value={item.value}
                    description={item.description}
                />
            ))}
        </div>
    );
}
