import "../styles/business-workspaces.css";
import { useEffect, useMemo, useState } from "react";
import { Building2, CheckCircle2, Layers3, RefreshCw, Search, Mail, Phone } from "lucide-react";
import api from "../api/axiosClient";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import FilterToolbar from "../components/ui/FilterToolbar";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";
import StatusBadge from "../components/ui/StatusBadge";
import Button from "../components/ui/Button";

export default function OemRegistry() {
    const { activeRole } = useAuth();
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("All");
    const [productFilter, setProductFilter] = useState("All");

    const load = async () => {
        try {
            setLoading(true);
            setError("");
            const response = await api.get("/oem/");
            if (!Array.isArray(response.data)) {
                throw new Error("The OEM Registry returned an unexpected response.");
            }
            setItems(response.data);
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load OEM Registry. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeRole === ROLES.SOLUTION_ENGINEER) load();
        else setLoading(false);
    }, [activeRole]);

    const statuses = useMemo(() => [...new Set(items.map((item) => item.status).filter(Boolean))], [items]);
    const products = useMemo(() => [...new Set(items.map((item) => item.product_name).filter(Boolean))], [items]);

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        return items.filter((item) => {
            const text = [
                item.partner_name, item.product_name, item.contact_person,
                item.email, item.phone, item.status, item.notes
            ].filter(Boolean).join(" ").toLowerCase();
            return (!q || text.includes(q))
                && (statusFilter === "All" || item.status === statusFilter)
                && (productFilter === "All" || item.product_name === productFilter);
        });
    }, [items, search, statusFilter, productFilter]);

    const activeCount = items.filter((item) => String(item.status || "").toLowerCase() === "active").length;

    if (activeRole !== ROLES.SOLUTION_ENGINEER) {
        return <div className="standard-page"><PageHeader title="OEM Registry" description="This workspace is available to Solution Engineers." /></div>;
    }

    return (
        <div className="standard-page business-workspace fade-in">
            <PageHeader
                title="OEM Registry"
                description="Read-only OEM partner records attached to your authorized accounts."
                actions={<Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={14} /> Refresh</Button>}
            />
            {error && <ErrorState message={error} onRetry={load} />}

            <div className="ui-kpi-grid">
                <KpiCard icon={Building2} label="Total OEMs" value={items.length} description="Registered partners" />
                <KpiCard icon={CheckCircle2} label="Active OEMs" value={activeCount} description="Currently active" />
                <KpiCard icon={Layers3} label="Products" value={products.length} description="Distinct partner products" />
                <KpiCard icon={Search} label="Showing" value={visible.length} description="Current result set" />
            </div>

            <SectionCard title="OEM Partners" description="Search and filter the OEM records returned by the backend." icon={Building2}>
                <FilterToolbar
                    search={{ icon: <Search size={14} />, value: search, onChange: (e) => setSearch(e.target.value) }}
                    placeholder="Search OEM, product, contact, email or phone…"
                    hasFilters={Boolean(search || statusFilter !== "All" || productFilter !== "All")}
                    onClear={() => { setSearch(""); setStatusFilter("All"); setProductFilter("All"); }}
                >
                    {statuses.length > 0 && (
                        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} aria-label="Filter by status">
                            <option value="All">All statuses</option>
                            {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
                        </select>
                    )}
                    {products.length > 0 && (
                        <select value={productFilter} onChange={(e) => setProductFilter(e.target.value)} aria-label="Filter by product">
                            <option value="All">All products</option>
                            {products.map((product) => <option key={product} value={product}>{product}</option>)}
                        </select>
                    )}
                </FilterToolbar>

                {loading ? (
                    <LoadingState message="Loading OEM partners…" />
                ) : error ? null : !visible.length ? (
                    <EmptyState message={search || statusFilter !== "All" || productFilter !== "All" ? "No OEM partners match the current filters." : "No OEM partners were returned for your authorized accounts."} />
                ) : (
                    <DataTable
                        columns={[
                            {
                                key: "partner",
                                label: "OEM",
                                render: (item) => <div className="ui-primary-cell"><strong>{item.partner_name || "Unnamed OEM"}</strong><span>Account #{item.account_id ?? "—"}</span></div>
                            },
                            { key: "product", label: "Product", render: (item) => <span className="ui-wrap-cell">{item.product_name || "—"}</span> },
                            {
                                key: "contact",
                                label: "Contact",
                                render: (item) => (
                                    <div className="ui-primary-cell">
                                        <strong>{item.contact_person || "—"}</strong>
                                        {item.email && <a href={`mailto:${item.email}`}><Mail size={12} />{item.email}</a>}
                                        {item.phone && <a href={`tel:${item.phone}`}><Phone size={12} />{item.phone}</a>}
                                    </div>
                                )
                            },
                            { key: "status", label: "Status", render: (item) => <StatusBadge status={item.status || "Not specified"} /> },
                            { key: "notes", label: "Notes", render: (item) => <span className="ui-wrap-cell">{item.notes || "—"}</span> }
                        ]}
                        rows={visible}
                        rowKey={(row) => row.oem_partner_id}
                    />
                )}
            </SectionCard>
        </div>
    );
}
