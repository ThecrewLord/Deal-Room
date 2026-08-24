export default function StatusBadge({ status }) {
    const value = String(status || "Unknown");
    const key = value.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    return <span className={`ui-status-badge ui-status-${key}`}>{value}</span>;
}
