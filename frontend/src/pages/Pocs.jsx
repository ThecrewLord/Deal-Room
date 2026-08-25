import "../styles/business-workspaces.css";
import { useEffect, useMemo, useState } from "react";
import { CalendarDays, CheckCircle2, Clock3, FlaskConical, ExternalLink, RefreshCw, Search, Target } from "lucide-react";
import { getOpportunities } from "../api/opportunityApi";
import { getPocsByOpportunity } from "../api/pocApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import FilterToolbar from "../components/ui/FilterToolbar";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";
import Button from "../components/ui/Button";

const STATUS_ORDER = ["Approved", "In Progress", "Submitted", "Completed", "Rejected"];

export default function Pocs() {
    const { activeRole } = useAuth();
    const [items, setItems] = useState([]);
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("All");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        try {
            setLoading(true);
            setError("");
            const opportunities = await getOpportunities();
            const groups = await Promise.all(
                opportunities.map(async (opportunity) => {
                    const pocs = await getPocsByOpportunity(opportunity.opportunity_id);
                    return pocs.map((poc) => ({
                        ...poc,
                        opportunity_name: opportunity.opportunity_name,
                        account_name: opportunity.account_name,
                    }));
                })
            );
            setItems(groups.flat());
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load POCs. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeRole === ROLES.SOLUTION_ENGINEER) load();
        else setLoading(false);
    }, [activeRole]);

    const statuses = useMemo(() => {
        const returned = [...new Set(items.map((item) => item.status).filter(Boolean))];
        return STATUS_ORDER.filter((status) => returned.includes(status))
            .concat(returned.filter((status) => !STATUS_ORDER.includes(status)));
    }, [items]);

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        return items.filter((item) => {
            const text = [
                item.poc_name, item.opportunity_name, item.account_name,
                item.status, item.outcome, item.objective
            ].filter(Boolean).join(" ").toLowerCase();
            return (!q || text.includes(q)) && (filter === "All" || item.status === filter);
        });
    }, [items, search, filter]);

    const completed = items.filter((item) => item.status === "Completed").length;
    const active = items.filter((item) => ["Approved", "In Progress", "Submitted"].includes(item.status)).length;

    if (activeRole !== ROLES.SOLUTION_ENGINEER) {
        return (
            <div className="standard-page">
                <PageHeader title="POC Tracker" description="This workspace is available to Solution Engineers." />
            </div>
        );
    }

    return (
        <div className="standard-page business-workspace fade-in">
            <PageHeader
                title="POC Tracker"
                description="Plan, execute and close technical proofs of concept."
                actions={<Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={14} /> Refresh</Button>}
            />

            {error && <ErrorState message={error} onRetry={load} />}

            <div className="ui-kpi-grid">
                <KpiCard icon={FlaskConical} label="Total POCs" value={items.length} description="Authorized opportunities" />
                <KpiCard icon={Clock3} label="Active / In Progress" value={active} description="Open technical work" />
                <KpiCard icon={CheckCircle2} label="Completed" value={completed} description="Finished POCs" />
                <KpiCard icon={Target} label="Showing" value={visible.length} description="Current result set" />
            </div>

            <SectionCard
                title="POC Worklist"
                description="Real POC records from your authorized opportunities."
                icon={FlaskConical}
            >
                <FilterToolbar
                    search={{ icon: <Search size={14} />, value: search, onChange: (e) => setSearch(e.target.value) }}
                    placeholder="Search POC, opportunity, account or status…"
                    hasFilters={Boolean(search || filter !== "All")}
                    onClear={() => { setSearch(""); setFilter("All"); }}
                >
                    <div className="ui-filter-pills">
                        <button type="button" className={filter === "All" ? "is-active" : ""} onClick={() => setFilter("All")}>All</button>
                        {statuses.map((status) => (
                            <button type="button" key={status} className={filter === status ? "is-active" : ""} onClick={() => setFilter(status)}>
                                {status}
                            </button>
                        ))}
                    </div>
                </FilterToolbar>

                {loading ? (
                    <LoadingState message="Loading POCs…" />
                ) : error ? null : !visible.length ? (
                    <EmptyState message={search || filter !== "All" ? "No POCs match your search or filter." : "No POCs found for your authorized opportunities."} />
                ) : (
                    <DataTable
                        columns={[
                            {
                                key: "poc",
                                label: "POC",
                                render: (poc) => <div className="ui-primary-cell"><strong>{poc.poc_name || "Untitled POC"}</strong><span>{poc.objective || "No objective provided"}</span></div>
                            },
                            {
                                key: "opportunity",
                                label: "Opportunity",
                                render: (poc) => <div className="ui-wrap-cell"><strong>{poc.opportunity_name || "—"}</strong><span>{poc.account_name || "—"}</span></div>
                            },
                            { key: "status", label: "Status", render: (poc) => <StatusBadge status={poc.status} /> },
                            { key: "target_date", label: "Target Date", render: (poc) => <span className="ui-icon-text"><CalendarDays size={13} />{poc.target_date || "—"}</span> },
                            { key: "outcome", label: "Outcome", render: (poc) => <span className="ui-wrap-cell">{poc.outcome || "Not completed"}</span> },
                            {
                                key: "actions",
                                label: "Action",
                                render: (poc) => <Button size="sm" variant="ghost" onClick={() => window.location.assign(`/opportunity/${poc.opportunity_id}`)}><ExternalLink size={13} /> Open</Button>
                            }
                        ]}
                        rows={visible}
                        rowKey={(row) => row.poc_id}
                    />
                )}
            </SectionCard>
        </div>
    );
}
