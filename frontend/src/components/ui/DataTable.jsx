import EmptyState from "./EmptyState";

export default function DataTable({ columns, rows, rowKey, emptyMessage = "No records found." }) {
    if (!rows?.length) return <EmptyState message={emptyMessage} />;
    return (
        <div className="ui-table-wrap">
            <table className="ui-data-table">
                <thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
                <tbody>{rows.map((row, index) => <tr key={rowKey ? rowKey(row) : index}>
                    {columns.map((column) => <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>)}
                </tr>)}</tbody>
            </table>
        </div>
    );
}
