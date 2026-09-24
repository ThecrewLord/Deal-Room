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
import { createStakeholder } from "../api/stakeholderApi";
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

    const [createStep, setCreateStep] = useState(1);

    const [stakeholder, setStakeholder] = useState({
        name: "",
        job_title: "",
        email: "",
        phone: "",
        company: "",
        tags: [],
    });

    const stakeholderTags = [
        "Economic Buyer",
        "Technical Champion",
        "End User",
        "Blocker",
        "Decision Maker",
    ];

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
            setError("");

            const accountId = form.account_id;

            if (!accountId) {
                setError("Select an existing canonical account.");
                setCreating(false);
                return;
            }

            if (!stakeholder.name.trim()) {
                setError("Stakeholder name is required.");
                setCreating(false);
                setCreateStep(2);
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

            await createStakeholder({
                ...stakeholder,
                opportunity_id: Number(created.opportunity_id),
            });

            setForm({
                account_id: "",
                opportunity_name: "",
                description: "",
                pain_points: "",
                estimated_value: "",
                probability: 0,
                expected_close_date: "",
            });

            setStakeholder({
                name: "",
                job_title: "",
                email: "",
                phone: "",
                company: "",
                tags: [],
            });

            setCreateStep(1);
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

    const toggleStakeholderTag = (tag) => {
        setStakeholder((current) => ({
            ...current,
            tags: current.tags.includes(tag)
                ? current.tags.filter((item) => item !== tag)
                : [...current.tags, tag],
        }));
    };


    const stages = [
        "Lead",
        "Qualified",
        "RFX",
        "POC",
        "Negotiations",
        "Delivery",
    ];

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
                    o.lifecycle_stage,
                    o.operational_status,
                    o.outcome,
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
                                    Create the opportunity, identify a key
                                    stakeholder, and review before saving.
                                </p>
                            </div>
                        </div>

                        {/* CREATION STEPS */}
                        <div className="opportunity-create-progress">
                            {[
                                [1, "Opportunity Details"],
                                [2, "Stakeholder"],
                                [3, "Review"],
                            ].map(([step, label]) => {
                                const completed = createStep > step;
                                const current = createStep === step;

                                return (
                                    <div
                                        key={step}
                                        className={`opportunity-create-step ${
                                            current
                                                ? "current"
                                                : completed
                                                ? "completed"
                                                : "future"
                                        }`}
                                    >
                                        <span className="opportunity-create-step-number">
                                            {completed ? "✓" : step}
                                        </span>
                                        <span>{label}</span>
                                    </div>
                                );
                            })}
                        </div>

                        {/* STEP 1 */}
                        {createStep === 1 && (
                            <div className="standard-form">
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

                                            {accounts
                                                .filter(
                                                    (a) =>
                                                        a.is_active !== false
                                                )
                                                .map((a) => (
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
                                            value={form.opportunity_name}
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
                                            step="0.01"
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
                                            onChange={(e) =>
                                                setForm({
                                                    ...form,
                                                    pain_points:
                                                        e.target.value,
                                                })
                                            }
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

                                        <textarea
                                            rows={3}
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
                                        type="button"
                                        onClick={() => {
                                            setError("");
                                            if (!form.account_id) {
                                                setError(
                                                    "Select an existing canonical account."
                                                );
                                                return;
                                            }
                                            if (
                                                !form.opportunity_name.trim()
                                            ) {
                                                setError(
                                                    "Opportunity name is required."
                                                );
                                                return;
                                            }
                                            if (
                                                form.estimated_value === ""
                                            ) {
                                                setError(
                                                    "Initial Opportunity Value is required."
                                                );
                                                return;
                                            }
                                            if (!form.pain_points.trim()) {
                                                setError(
                                                    "Pain points are required."
                                                );
                                                return;
                                            }
                                            setCreateStep(2);
                                        }}
                                    >
                                        Next: Stakeholder
                                    </Button>
                                </div>
                            </div>
                        )}

                        {/* STEP 2 */}
                        {createStep === 2 && (
                            <div className="standard-form">
                                <div className="field-grid">

                                    <label className="field-label">
                                        Stakeholder name

                                        <input
                                            required
                                            value={stakeholder.name}
                                            onChange={(e) =>
                                                setStakeholder({
                                                    ...stakeholder,
                                                    name: e.target.value,
                                                })
                                            }
                                            placeholder="Customer stakeholder"
                                        />
                                    </label>

                                    <label className="field-label">
                                        Job title

                                        <input
                                            value={stakeholder.job_title}
                                            onChange={(e) =>
                                                setStakeholder({
                                                    ...stakeholder,
                                                    job_title:
                                                        e.target.value,
                                                })
                                            }
                                        />
                                    </label>

                                    <label className="field-label">
                                        Email

                                        <input
                                            type="email"
                                            value={stakeholder.email}
                                            onChange={(e) =>
                                                setStakeholder({
                                                    ...stakeholder,
                                                    email: e.target.value,
                                                })
                                            }
                                        />
                                    </label>

                                    <label className="field-label">
                                        Phone

                                        <input
                                            value={stakeholder.phone}
                                            onChange={(e) =>
                                                setStakeholder({
                                                    ...stakeholder,
                                                    phone: e.target.value,
                                                })
                                            }
                                        />
                                    </label>

                                    <label className="field-label">
                                        Company

                                        <input
                                            value={stakeholder.company}
                                            onChange={(e) =>
                                                setStakeholder({
                                                    ...stakeholder,
                                                    company:
                                                        e.target.value,
                                                })
                                            }
                                        />
                                    </label>

                                </div>

                                <div style={{ marginTop: 16 }}>
                                    <strong>Stakeholder tags</strong>

                                    <div
                                        style={{
                                            display: "flex",
                                            gap: 8,
                                            flexWrap: "wrap",
                                            marginTop: 10,
                                        }}
                                    >
                                        {stakeholderTags.map((tag) => (
                                            <button
                                                type="button"
                                                key={tag}
                                                className={
                                                    stakeholder.tags.includes(
                                                        tag
                                                    )
                                                        ? "tag-selected"
                                                        : ""
                                                }
                                                onClick={() =>
                                                    toggleStakeholderTag(
                                                        tag
                                                    )
                                                }
                                            >
                                                {tag}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="record-actions">
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        onClick={() => {
                                            setError("");
                                            setCreateStep(1);
                                        }}
                                    >
                                        Back
                                    </Button>

                                    <Button
                                        type="button"
                                        onClick={() => {
                                            setError("");

                                            if (
                                                !stakeholder.name.trim()
                                            ) {
                                                setError(
                                                    "Stakeholder name is required."
                                                );
                                                return;
                                            }

                                            setCreateStep(3);
                                        }}
                                    >
                                        Next: Review
                                    </Button>
                                </div>
                            </div>
                        )}

                        {/* STEP 3 */}
                        {createStep === 3 && (
                            <form
                                className="standard-form"
                                onSubmit={submit}
                            >
                                <div
                                    style={{
                                        padding: 16,
                                        border: "1px solid #ddd",
                                        borderRadius: 10,
                                    }}
                                >
                                    <h3>Review Opportunity</h3>

                                    <p>
                                        <strong>Account:</strong>{" "}
                                        {accounts.find(
                                            (a) =>
                                                String(a.account_id) ===
                                                String(form.account_id)
                                        )?.account_name || "—"}
                                    </p>

                                    <p>
                                        <strong>Opportunity:</strong>{" "}
                                        {form.opportunity_name}
                                    </p>

                                    <p>
                                        <strong>Initial Value:</strong>{" "}
                                        {form.estimated_value}
                                    </p>

                                    <p>
                                        <strong>Probability:</strong>{" "}
                                        {form.probability || 0}%
                                    </p>

                                    <p>
                                        <strong>Expected Close:</strong>{" "}
                                        {form.expected_close_date || "—"}
                                    </p>

                                    <p>
                                        <strong>Pain Points:</strong>{" "}
                                        {form.pain_points || "—"}
                                    </p>

                                    <hr />

                                    <h3>Stakeholder</h3>

                                    <p>
                                        <strong>Name:</strong>{" "}
                                        {stakeholder.name}
                                    </p>

                                    <p>
                                        <strong>Job Title:</strong>{" "}
                                        {stakeholder.job_title || "—"}
                                    </p>

                                    <p>
                                        <strong>Email:</strong>{" "}
                                        {stakeholder.email || "—"}
                                    </p>

                                    <p>
                                        <strong>Company:</strong>{" "}
                                        {stakeholder.company || "—"}
                                    </p>

                                    <p>
                                        <strong>Tags:</strong>{" "}
                                        {stakeholder.tags.length
                                            ? stakeholder.tags.join(", ")
                                            : "None"}
                                    </p>
                                </div>

                                <div className="record-actions">
                                    <Button
                                        type="button"
                                        variant="secondary"
                                        onClick={() => {
                                            setError("");
                                            setCreateStep(2);
                                        }}
                                        disabled={creating}
                                    >
                                        Back
                                    </Button>

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
                        )}
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
                <th>Deal Finder</th>
                <th>Owner</th>
                <th>Lifecycle</th>
                <th>Operational</th>
                <th>Outcome</th>
                <th>Value</th>
                <th>Expected Close</th>
                <th>Age</th>
                <th>Last Activity</th>
                <th>Stalled</th>
                <th></th>
            </tr>
        </thead>

        <tbody>

            {loading ? (
                <tr>
                    <td
                        colSpan="13"
                        className="opportunity-loading"
                    >
                        Loading opportunities...
                    </td>
                </tr>
            ) : (
                visible.map((o) => {

                    const createdAt = o.created_at
                        ? new Date(o.created_at)
                        : null;

                    const ageDays = createdAt
                        ? Math.max(
                              0,
                              Math.floor(
                                  (Date.now() - createdAt.getTime()) /
                                      (1000 * 60 * 60 * 24)
                              )
                          )
                        : "—";

                    const isStalled =
                        o.operational_status === "Stalled";

                    return (
                        <tr
                            key={o.opportunity_id}
                            onClick={() =>
                                navigate(
                                    `/opportunity/${o.opportunity_id}`
                                )
                            }
                            className="opportunity-table-row"
                        >

                            {/* Opportunity */}
                            <td>
                                <div className="opportunity-name">
                                    <strong>
                                        {o.opportunity_name}
                                    </strong>

                                    <span>
                                        Opportunity #
                                        {o.opportunity_id}
                                    </span>
                                </div>
                            </td>

                            {/* Account */}
                            <td>
                                <span className="opportunity-account">
                                    {o.account_name ||
                                        `Account #${o.account_id}`}
                                </span>
                            </td>

                            {/* Deal Finder */}
                            <td>
                                {o.deal_finder ? (
                                    <div className="opportunity-owner-cell">
                                        <div className="opportunity-owner-avatar">
                                            {o.deal_finder.full_name
                                                ?.charAt(0)
                                                ?.toUpperCase() || "U"}
                                        </div>

                                        <span>
                                            {o.deal_finder.full_name}
                                        </span>
                                    </div>
                                ) : (
                                    <span className="opportunity-owner-empty">
                                        Unassigned
                                    </span>
                                )}
                            </td>

                            {/* Owner */}
                            <td>
                                {o.sales_owner ? (
                                    <div className="opportunity-owner-cell">
                                        <div className="opportunity-owner-avatar">
                                            {o.sales_owner.full_name
                                                ?.charAt(0)
                                                ?.toUpperCase() || "U"}
                                        </div>

                                        <span>
                                            {o.sales_owner.full_name}
                                        </span>
                                    </div>
                                ) : (
                                    <span className="opportunity-owner-empty">
                                        Unassigned
                                    </span>
                                )}
                            </td>

                            {/* Lifecycle */}
                            <td>
                                <StageBadge
                                    stage={o.lifecycle_stage}
                                />
                            </td>

                            {/* Operational Status */}
                            <td>
                                <StatusBadge
                                    status={o.operational_status}
                                />
                            </td>

                            {/* Outcome */}
                            <td>
                                <StatusBadge
                                    status={o.outcome}
                                />
                            </td>

                            {/* Value */}
                            <td>
                                ₹
                                {Number(
                                    o.estimated_value || 0
                                ).toLocaleString("en-IN")}
                            </td>

                            {/* Expected Close */}
                            <td>
                                {o.expected_close_date
                                    ? new Date(
                                          o.expected_close_date
                                      ).toLocaleDateString("en-IN")
                                    : "—"}
                            </td>

                            {/* Age */}
                            <td>
                                {ageDays === "—"
                                    ? "—"
                                    : `${ageDays}d`}
                            </td>

                            {/* Last Activity */}
                            <td>
                                {o.last_activity
                                    ? new Date(
                                          o.last_activity
                                      ).toLocaleDateString("en-IN")
                                    : "—"}
                            </td>

                            {/* Stalled */}
                            <td>
                                <StatusBadge
                                    status={
                                        isStalled
                                            ? "Stalled"
                                            : "Active"
                                    }
                                />
                            </td>

                            {/* Open */}
                            <td>
                                <div className="opportunity-arrow">
                                    <ChevronRight size={16} />
                                </div>
                            </td>

                        </tr>
                    );
                })
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
