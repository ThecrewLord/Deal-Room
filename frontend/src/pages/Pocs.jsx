import "../styles/business-workspaces.css";
import { useEffect, useMemo, useState } from "react";
import {
    CalendarDays,
    CheckCircle2,
    Clock3,
    FlaskConical,
    ExternalLink,
    RefreshCw,
    Search,
    Target,
} from "lucide-react";
import { getOpportunities } from "../api/opportunityApi";
import { getPocsByOpportunity, getAssignedPocs } from "../api/pocApi";
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

const STATUS_ORDER = ["Draft", "In Progress", "Submitted", "Completed"];
const FINAL_POC_OUTCOMES = new Set(["Success", "Failure"]);
const hasFinalPocOutcome = (poc) => poc.status === "Completed" && FINAL_POC_OUTCOMES.has(poc.outcome);
const timestamp = (value) => {
    if (!value) return 0;
    const parsed = Date.parse(value);
    return Number.isNaN(parsed) ? 0 : parsed;
};
const orderPocs = (pocs) => [...pocs].sort((a, b) => {
    const aCompleted = hasFinalPocOutcome(a);
    const bCompleted = hasFinalPocOutcome(b);
    if (aCompleted !== bCompleted) return aCompleted ? 1 : -1;
    const aDate = aCompleted ? (a.updated_at || a.submitted_at || a.created_at) : a.created_at;
    const bDate = bCompleted ? (b.updated_at || b.submitted_at || b.created_at) : b.created_at;
    const dateDifference = timestamp(bDate) - timestamp(aDate);
    return dateDifference || Number(b.poc_id || 0) - Number(a.poc_id || 0);
});

export default function Pocs() {
    const { activeRole } = useAuth();

    const [items, setItems] = useState([]);
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("All");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [expandedPocs, setExpandedPocs] = useState(new Set());

    const load = async () => {
        try {
            setLoading(true);
            setError("");

            const pocs = await getAssignedPocs();

            const opportunities = await getOpportunities().catch(() => []);
            const opportunityMap = new Map(
                opportunities.map((o) => [
                    o.opportunity_id,
                    {
                        opportunity_name: o.opportunity_name,
                        account_name: o.account_name,
                    },
                ])
            );

            setItems(
                pocs.map((poc) => ({
                    ...poc,
                    ...(opportunityMap.get(poc.opportunity_id) || {}),
                }))
            );
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load POCs. Please try again.");
        } finally {
            setLoading(false);
        }
    };


    useEffect(() => {
        if ([ROLES.SOLUTION_ENGINEER,ROLES.DELIVERY_MANAGER,ROLES.DEVOPS_ENGINEER,ROLES.DATA_ANALYST].includes(activeRole)) load();
        else setLoading(false);
    }, [activeRole]);

    const togglePoc = (pocId) => {
        setExpandedPocs((current) => {
            const next = new Set(current);

            if (next.has(pocId)) {
                next.delete(pocId);
            } else {
                next.add(pocId);
            }

            return next;
        });
    };

    const isCompletedPoc = hasFinalPocOutcome;

    const statuses = useMemo(() => {
        const returned = [...new Set(items.map((item) => item.status).filter(Boolean))];
        return STATUS_ORDER.filter((status) => returned.includes(status))
            .concat(returned.filter((status) => !STATUS_ORDER.includes(status)));
    }, [items]);

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        return orderPocs(items).filter((item) => {
            const text = [
                item.poc_name, item.opportunity_name, item.account_name,
                item.status, item.outcome, item.objective
            ].filter(Boolean).join(" ").toLowerCase();
            return (!q || text.includes(q)) && (filter === "All" || item.status === filter);
        });
    }, [items, search, filter]);

    const completed = items.filter((item) => item.status === "Completed").length;
    const active = items.filter((item) => ["Draft", "In Progress", "Submitted"].includes(item.status)).length;

    if (![ROLES.SOLUTION_ENGINEER,ROLES.DELIVERY_MANAGER,ROLES.DEVOPS_ENGINEER,ROLES.DATA_ANALYST].includes(activeRole)) {
        return (
            <div className="standard-page">
                <PageHeader title="POC Tracker" description="POC workspace for Solution Engineers, Delivery Managers and assigned execution members." />
            </div>
        );
    }

    return (
        <div className="standard-page business-workspace fade-in">
            <PageHeader
    title="POC Tracker"
    description="Plan, execute and close technical proofs of concept."
    actions={
        <div className="poc-header-actions">
            <Button
                variant="secondary"
                onClick={load}
                disabled={loading}
            >
                <RefreshCw size={14} />
                Refresh
            </Button>
        </div>
    }
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
                                render: (poc) => {
                                    const completed = isCompletedPoc(poc);
                                    const expanded = expandedPocs.has(poc.poc_id);

                                    return (
                                        <div
                                            className={`poc-worklist-cell ${completed ? "poc-completed-cell" : ""}`}
                                            onClick={() => completed && togglePoc(poc.poc_id)}
                                            role={completed ? "button" : undefined}
                                            tabIndex={completed ? 0 : undefined}
                                            onKeyDown={(e) => {
                                                if (completed && (e.key === "Enter" || e.key === " ")) {
                                                    e.preventDefault();
                                                    togglePoc(poc.poc_id);
                                                }
                                            }}
                                        >
                                            <div className="poc-worklist-title">
                                                {completed && (
                                                    <span className="poc-expand-icon">
                                                        {expanded ? "▾" : "▸"}
                                                    </span>
                                                )}
                                                <strong>{poc.poc_name || "Untitled POC"}</strong>
                                            </div>

                                            {(!completed || expanded) && (
                                                <span>{poc.objective || "No objective provided"}</span>
                                            )}
                                        </div>
                                    );
                                }
                            },
                            {
                                key: "opportunity",
                                label: "Opportunity",
                                render: (poc) => {
                                    const completed = isCompletedPoc(poc);
                                    const expanded = expandedPocs.has(poc.poc_id);

                                    return (
                                        <div
                                            className={`ui-wrap-cell ${completed ? "poc-completed-cell" : ""}`}
                                            onClick={() => completed && togglePoc(poc.poc_id)}
                                        >
                                            <strong>{poc.opportunity_name || "—"}</strong>
                                            {(!completed || expanded) && (
                                                <span>{poc.account_name || "—"}</span>
                                            )}
                                        </div>
                                    );
                                }
                            },
                            {
                                key: "status",
                                label: "Status",
                                render: (poc) => (
                                    <div
                                        className={isCompletedPoc(poc) ? "poc-completed-cell" : ""}
                                        onClick={() => isCompletedPoc(poc) && togglePoc(poc.poc_id)}
                                    >
                                        <StatusBadge status={poc.status} />
                                    </div>
                                )
                            },
                            {
                                key: "target_date",
                                label: "Target Date",
                                render: (poc) => {
                                    const completed = isCompletedPoc(poc);
                                    const expanded = expandedPocs.has(poc.poc_id);

                                    return (
                                        <div
                                            className={completed ? "poc-completed-cell" : ""}
                                            onClick={() => completed && togglePoc(poc.poc_id)}
                                        >
                                            {(!completed || expanded) && (
                                                <span className="ui-icon-text">
                                                    <CalendarDays size={13} />
                                                    {poc.target_date || "—"}
                                                </span>
                                            )}
                                            {completed && !expanded && (
                                                <span className="poc-collapsed-label">
                                                    Completed
                                                </span>
                                            )}
                                        </div>
                                    );
                                }
                            },
                            {
                                key: "outcome",
                                label: "Outcome",
                                render: (poc) => {
                                    const completed = isCompletedPoc(poc);
                                    const expanded = expandedPocs.has(poc.poc_id);

                                    return (
                                        <div
                                            className={`ui-wrap-cell ${completed ? "poc-completed-cell" : ""}`}
                                            onClick={() => completed && togglePoc(poc.poc_id)}
                                        >
                                            <strong>{poc.outcome || "Not completed"}</strong>

                                            {completed && !expanded && (
                                                <span className="poc-collapsed-hint">
                                                    Click to expand
                                                </span>
                                            )}
                                        </div>
                                    );
                                }
                            },
                            {
                                key: "actions",
                                label: "Action",
                                render: (poc) => (
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => window.location.assign(`/opportunity/${poc.opportunity_id}`)}
                                    >
                                        <ExternalLink size={13} /> Open
                                    </Button>
                                )
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
