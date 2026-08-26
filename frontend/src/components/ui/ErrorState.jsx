import { AlertTriangle, RefreshCw } from "lucide-react";

export default function ErrorState({ title = "Unable to load data", message = "Something went wrong while loading this workspace.", onRetry }) {
    return (
        <div className="ui-error-state" role="alert">
            <span className="ui-error-icon"><AlertTriangle size={17} /></span>
            <div>
                <strong>{title}</strong>
                <p>{message}</p>
                {onRetry && <button type="button" className="ui-error-retry" onClick={onRetry}><RefreshCw size={13} /> Retry</button>}
            </div>
        </div>
    );
}
