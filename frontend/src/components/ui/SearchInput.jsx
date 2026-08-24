import { Search, X } from "lucide-react";

export default function SearchInput({ value, onChange, placeholder = "Search...", className = "" }) {
    return (
        <div className={`ui-search ${className}`}>
            <Search size={15} />
            <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} aria-label={placeholder} />
            {value && <button type="button" onClick={() => onChange("")} aria-label="Clear search"><X size={13} /></button>}
        </div>
    );
}
