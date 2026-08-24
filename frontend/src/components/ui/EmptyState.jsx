import { Inbox } from "lucide-react";

export default function EmptyState({ message, icon: Icon = Inbox }) {
    return (
        <div className="ui-empty-state">
            <span className="ui-empty-icon"><Icon size={17} /></span>
            <span>{message}</span>
        </div>
    );
}
