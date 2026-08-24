import StatusBadge from "./StatusBadge";

export default function StageBadge({ stage }) {
    return <StatusBadge status={stage || "Unassigned"} />;
}
