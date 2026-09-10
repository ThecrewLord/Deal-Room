import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Opportunities.css";
import {
    Search,
    RefreshCw,
    TrendingUp,
    CheckCircle2,
    CircleDollarSign,
    XCircle,
    ChevronRight,
} from "lucide-react";

import { createOpportunity, getOpportunities } from "../api/opportunityApi";
import { getAccounts } from "../api/accountApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";

import Button from "../components/ui/Button";
import SearchInput from "../components/ui/SearchInput";
import StageBadge from "../components/ui/StageBadge";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";

export default function Opportunities() {
    const { activeRole } = useAuth();
    const navigate = useNavigate();

    const [opportunities, setOpportunities] = useState([]);
    const [accounts, setAccounts] = useState([]);

    const [search, setSearch] = useState("");
    const [stageFilter, setStageFilter] = useState("all");
    const [statusFilter, setStatusFilter] = useState("all");

    const [showCreate, setShowCreate] = useState(false);
    const [error, setError] = useState("");
    const [creating, setCreating] = useState(false);
    const [loading, setLoading] = useState(true);

    const canCreateLead = [
        ROLES.LEADERSHIP, ROLES.SALES_MANAGER, ROLES.SALES_EXECUTIVE,
        ROLES.PRE_SALES_MANAGER, ROLES.SOLUTION_ENGINEER, ROLES.DELIVERY_MANAGER,
        ROLES.DEVOPS_ENGINEER, ROLES.DATA_ANALYST,
    ].includes(activeRole);

    const [form, setForm] = useState({
        account_id: "",
        opportunity_name: "",
        description: "",
        pain_points: "",
        estimated_value: "",
        probability: 0,
        expected_close_date: "",
    });

    const load = async () => {
        try {
            setError("");
            setLoading(true);

            const data = await getOpportunities();
            setOpportunities(data || []);

            if (canCreateLead) {
                setAccounts(await getAccounts());
            }
        } catch (err) {
            setError(
                err.response?.data?.message ||
                "Unable to load opportunities."
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [activeRole]);

    const submit = async (e) => {
        e.preventDefault();

        try {
            setCreating(true);

            const accountId = form.account_id;
            if (!accountId) {
                setError("Select an existing canonical account.");
                return;
            }

            const created = await createOpportunity({
                ...form,
                account_id: Number(accountId),
                estimated_value: form.estimated_value,
                pain_points: form.pain_points || null,
                probability: Number(form.probability || 0),
                expected_close_date: form.expected_close_date || null,
            });

            setForm({
                account_id: "",
                opportunity_name: "",
                description: "",
                estimated_value: "",
                pain_points: "",
                probability: 0,
                expected_close_date: "",
            });

            setShowCreate(false);

            navigate(`/opportunity/${created.opportunity_id}`);
        } catch (err) {
            setError(
                err.response?.data?.message ||
                "Unable to create opportunity."
            );
        } finally {
            setCreating(false);
        }
    };

    const stages = useMemo(() => {
        const values = opportunities
            .map((o) => o.lifecycle_stage)
            .filter(Boolean);

        return [...new Set(values)];
    }, [opportunities]);

    const stats = useMemo(() => {
        const total = opportunities.length;

        const open = opportunities.filter(
            (o) => o.outcome === "Open" && o.operational_status === "Active"
        ).length;

        const won = opportunities.filter((o) => o.outcome === "Closed Won").length;

        const lost = opportunities.filter((o) => o.outcome === "Closed Lost").length;

        return { total, open, won, lost };
    }, [opportunities]);

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();

        return opportunities.filter((o) => {
            const matchesSearch =
                !q ||
                [
                    o.opportunity_name,
                    o.status,
                    o.lifecycle_stage,
                    o.account_name,
                    o.sales_owner?.full_name,
                ]
                    .filter(Boolean)
                    .some((v) =>
                        String(v).toLowerCase().includes(q)
                    );

            const matchesStage =
                stageFilter === "all" ||
                o.lifecycle_stage === stageFilter;

            const normalizedOutcome = String(o.outcome || "").toLowerCase();
            const normalizedOperationalStatus = String(o.operational_status || "").toLowerCase();
            const matchesStatus =
                statusFilter === "all" ||
                (statusFilter.toLowerCase() === "open" && normalizedOutcome === "open" && normalizedOperationalStatus === "active") ||
                normalizedOutcome === statusFilter.toLowerCase();

            return (
                matchesSearch &&
                matchesStage &&
                matchesStatus
            );
        });
    }, [
        opportunities,
        search,
        stageFilter,
        statusFilter,
    ]);

    return (
        <div className="opportunities-page">

            {/* PAGE HEADER */}
            <div className="opportunities-header">
                <div>
                    <div className="opportunities-eyebrow">
                        SALES PIPELINE
                    </div>

                    <h1>Opportunities</h1>

                    <p>
                        Manage and track sales opportunities visible
                        to your active role.
                    </p>
                </div>

                <div className="opportunities-header-actions">
                    {canCreateLead && (
                        <Button
                            variant={showCreate ? "danger" : "primary"}
                            onClick={() =>
                                setShowCreate((value) => !value)
                            }
                        >
                            {showCreate ? "Close" : "New Opportunity"}
                        </Button>
                    )}

                    <Button
                        variant="secondary"
                        onClick={load}
                        disabled={loading}
                    >
                        <RefreshCw
                            size={14}
                            className={
                                loading
                                    ? "opportunity-spin"
                                    : ""
                            }
                        />
                        Refresh
                    </Button>
                </div>
            </div>

            {/* ERROR */}
            {error && (
                <div className="opportunities-error">
                    {error}
                </div>
            )}

            {/* KPI CARDS */}
            <div className="opportunity-stats">

                <div className="opportunity-stat-card">
                    <div className="opportunity-stat-icon blue">
                        <TrendingUp size={18} />
                    </div>

                    <div>
                        <span>Total Opportunities</span>
                        <strong>{stats.total}</strong>
                    </div>
                </div>

                <div className="opportunity-stat-card">
                    <div className="opportunity-stat-icon green">
                        <CircleDollarSign size={18} />
                    </div>

                    <div>
                        <span>Open Deals</span>
                        <strong>{stats.open}</strong>
                    </div>
                </div>

                <div className="opportunity-stat-card">
                    <div className="opportunity-stat-icon emerald">
                        <CheckCircle2 size={18} />
                    </div>

                    <div>
                        <span>Closed Won</span>
                        <strong>{stats.won}</strong>
                    </div>
                </div>

                <div className="opportunity-stat-card">
                    <div className="opportunity-stat-icon red">
                        <XCircle size={18} />
                    </div>

                    <div>
                        <span>Closed Lost</span>
                        <strong>{stats.lost}</strong>
                    </div>
                </div>

            </div>

            {/* CREATE FORM */}
            {showCreate &&
                canCreateLead && (
                    <div className="opportunity-create-card">

                        <div className="opportunity-create-header">
                            <div>
                                <span className="opportunities-eyebrow">
                                    CREATE
                                </span>

                                <h2>New Opportunity</h2>

                                <p>
                                    Add a new sales opportunity
                                    to the pipeline.
                                </p>
                            </div>
                        </div>

                        <form
                            className="standard-form"
                            onSubmit={submit}
                        >
                            <div className="field-grid">

                                <label className="field-label">
                                    Account

                                    <select
                                        required
                                        value={form.account_id}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                account_id:
                                                    e.target.value,
                                            })
                                        }
                                    >
                                        <option value="">
                                            Select account
                                        </option>

                                        {accounts.filter((a) => a.is_active !== false).map((a) => (
                                            <option
                                                key={a.account_id}
                                                value={a.account_id}
                                            >
                                                {a.account_name}
                                            </option>
                                        ))}
                                    </select>
                                </label>

                                <label className="field-label">
                                    Opportunity name

                                    <input
                                        required
                                        minLength={2}
                                        value={
                                            form.opportunity_name
                                        }
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                opportunity_name:
                                                    e.target.value,
                                            })
                                        }
                                    />
                                </label>

                                <label className="field-label">
                                    Initial Opportunity Value

                                    <input
                                        type="number"
                                        min="0"
                                        required
                                        value={form.estimated_value}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                estimated_value:
                                                    e.target.value,
                                            })
                                        }
                                    />
                                </label>

                                <label className="field-label">
                                    Pain points

                                    <textarea
                                        required
                                        rows={3}
                                        value={form.pain_points}
                                        onChange={(e) => setForm({ ...form, pain_points: e.target.value })}
                                        placeholder="What customer problem is this opportunity solving?"
                                    />
                                </label>

                                <label className="field-label">
                                    Probability %

                                    <input
                                        type="number"
                                        min="0"
                                        max="100"
                                        value={form.probability}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                probability:
                                                    e.target.value,
                                            })
                                        }
                                    />
                                </label>

                                <label className="field-label">
                                    Expected close

                                    <input
                                        type="date"
                                        value={
                                            form.expected_close_date
                                        }
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                expected_close_date:
                                                    e.target.value,
                                            })
                                        }
                                    />
                                </label>

                                <label className="field-label">
                                    Description

                                    <input
                                        value={form.description}
                                        onChange={(e) =>
                                            setForm({
                                                ...form,
                                                description:
                                                    e.target.value,
                                            })
                                        }
                                    />
                                </label>

                            </div>

                            <div className="record-actions">
                                <Button
                                    type="submit"
                                    disabled={creating}
                                >
                                    {creating
                                        ? "Creating..."
                                        : "Create Opportunity"}
                                </Button>
                            </div>
                        </form>
                    </div>
                )}

            {/* OPPORTUNITY TABLE */}
            <div className="opportunity-table-card">

                {/* TOOLBAR */}
                <div className="opportunity-toolbar">

                    <div className="opportunity-toolbar-left">
                        <div>
                            <h2>Sales Opportunities</h2>
                            <span>
                                {visible.length} opportunities
                            </span>
                        </div>
                    </div>

                    <div className="opportunity-filters">

                        <SearchInput
                            value={search}
                            onChange={setSearch}
                            placeholder="Search opportunities..."
                        />

                        <select
                            className="opportunity-filter"
                            value={stageFilter}
                            onChange={(e) =>
                                setStageFilter(e.target.value)
                            }
                        >
                            <option value="all">
                                All stages
                            </option>

                            {stages.map((stage) => (
                                <option
                                    key={stage}
                                    value={stage}
                                >
                                    {stage}
                                </option>
                            ))}
                        </select>

                        <select
                            className="opportunity-filter"
                            value={statusFilter}
                            onChange={(e) =>
                                setStatusFilter(e.target.value)
                            }
                        >
                            <option value="all">
                                All status
                            </option>

                            <option value="open">
                                Open
                            </option>

                            <option value="closed won">
                                Closed Won
                            </option>

                            <option value="closed lost">
                                Closed Lost
                            </option>
                        </select>

                    </div>
                </div>

                {/* TABLE */}
                <div className="opportunity-table-wrapper">

                    <table className="opportunity-table">

                        <thead>
                            <tr>
                                <th>Opportunity</th>
                                <th>Account</th>
                                <th>Stage</th>
                                <th>Status</th>
                                <th>Owner</th>
                                <th></th>
                            </tr>
                        </thead>

                        <tbody>

                            {loading ? (
                                <tr>
                                    <td
                                        colSpan="6"
                                        className="opportunity-loading"
                                    >
                                        Loading opportunities...
                                    </td>
                                </tr>
                            ) : (
                                visible.map((o) => (
                                    <tr
                                        key={o.opportunity_id}
                                        onClick={() =>
                                            navigate(
                                                `/opportunity/${o.opportunity_id}`
                                            )
                                        }
                                        className="opportunity-table-row"
                                    >

                                        <td>
                                            <div className="opportunity-name">
                                                <strong>
                                                    {
                                                        o.opportunity_name
                                                    }
                                                </strong>

                                                <span>
                                                    Opportunity #
                                                    {
                                                        o.opportunity_id
                                                    }
                                                </span>
                                            </div>
                                        </td>

                                        <td>
                                            <span className="opportunity-account">
                                                {o.account_name ||
                                                    `Account #${o.account_id}`}
                                            </span>
                                        </td>

                                        <td>
                                            <StageBadge
                                                stage={o.lifecycle_stage}
                                            />
                                        </td>

                                        <td>
                                            <StatusBadge
                                                status={o.outcome || o.operational_status}
                                            />
                                        </td>

                                        <td>
                                            {o.sales_owner ? (
                                                <div className="opportunity-owner-cell">

                                                    <div className="opportunity-owner-avatar">
                                                        {o.sales_owner.full_name
                                                            ?.charAt(0)
                                                            ?.toUpperCase() ||
                                                            "U"}
                                                    </div>

                                                    <span>
                                                        {
                                                            o.sales_owner
                                                                .full_name
                                                        }
                                                    </span>

                                                </div>
                                            ) : (
                                                <span className="opportunity-owner-empty">
                                                    Unassigned
                                                </span>
                                            )}
                                        </td>

                                        <td>
                                            <div className="opportunity-arrow">
                                                <ChevronRight
                                                    size={16}
                                                />
                                            </div>
                                        </td>

                                    </tr>
                                ))
                            )}

                        </tbody>

                    </table>

                    {!loading && !visible.length && (
                        <div className="opportunity-empty">
                            <EmptyState
                                message={
                                    search
                                        ? "No matching opportunities"
                                        : "No visible opportunities"
                                }
                            />
                        </div>
                    )}

                </div>

            </div>
        </div>
    );
}