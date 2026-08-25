import { LoaderCircle } from "lucide-react";

export default function LoadingState({ message = "Loading…", compact = false }) {
    return (
        <div className={`ui-loading-state ${compact ? "is-compact" : ""}`} role="status">
            <LoaderCircle className="ui-spin" size={compact ? 16 : 20} />
            <span>{message}</span>
        </div>
    );
}
