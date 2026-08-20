import {
    ResponsiveContainer,
    PieChart,
    Pie,
    Tooltip,
    Cell,
} from "recharts";

import SectionCard from "./SectionCard";
import EmptyState from "./EmptyState";

const COLORS = [
    "#2563eb",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
];

const TeamPerformance = ({ dashboard }) => {
    if (!dashboard?.team_performance?.length) {
        return (
            <SectionCard title="Team Performance">
                <EmptyState
                    title="No performance data"
                    subtitle="Team metrics will appear here."
                />
            </SectionCard>
        );
    }

    const chartData = dashboard.team_performance.map((item) => ({
        name: item.label,
        value: item.value,
    }));

    return (
        <SectionCard title="Team Performance">
            <div className="team-performance-grid">
                {dashboard.team_performance.map((item) => (
                    <div
                        key={item.label}
                        className="pipeline-card"
                    >
                        <span>{item.label}</span>

                        <h3>{item.value}</h3>
                    </div>
                ))}
            </div>

            <div className="dashboard-chart">
                <ResponsiveContainer
                    width="100%"
                    height={300}
                >
                    <PieChart>
                        <Pie
                            data={chartData}
                            dataKey="value"
                            nameKey="name"
                            outerRadius={90}
                            label
                        >
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={entry.name}
                                    fill={
                                        COLORS[
                                            index % COLORS.length
                                        ]
                                    }
                                />
                            ))}
                        </Pie>

                        <Tooltip />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </SectionCard>
    );
};

export default TeamPerformance;