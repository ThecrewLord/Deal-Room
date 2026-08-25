import { TrendingDown, TrendingUp } from "lucide-react";

export default function KpiCard({ icon: Icon, label, value, description, trend, tone = "blue", className = "" }) {
    const trendValue = trend?.value;
    const trendUp = trend?.direction === "up";
    return (
        <section className={`ui-kpi-card ui-kpi-tone-${tone} ${className}`} aria-label={label}>
            {Icon && <span className="ui-kpi-icon"><Icon size={17} /></span>}
            <div className="ui-kpi-content">
                <span className="ui-kpi-label">{label}</span>
                <strong className="ui-kpi-value">{value ?? "—"}</strong>
                {description && <span className="ui-kpi-description">{description}</span>}
                {trendValue != null && (
                    <span className={`ui-kpi-trend ${trendUp ? "is-up" : "is-down"}`}>
                        {trendUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                        {trendValue}
                    </span>
                )}
            </div>
        </section>
    );
}
