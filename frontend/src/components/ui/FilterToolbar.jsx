export default function FilterToolbar({ search, children, onClear, hasFilters = false, placeholder = "Search…" }) {
    return (
        <div className="ui-filter-toolbar">
            {search && (
                <label className="ui-search ui-filter-search">
                    {search.icon}
                    <input value={search.value} onChange={search.onChange} placeholder={placeholder} />
                    {search.value && <button type="button" onClick={() => search.onChange({ target: { value: "" } })} aria-label="Clear search">×</button>}
                </label>
            )}
            <div className="ui-filter-controls">{children}</div>
            {hasFilters && onClear && <button type="button" className="ui-clear-filter" onClick={onClear}>Clear filters</button>}
        </div>
    );
}
