import "../styles/business-workspaces.css";
import { useEffect, useMemo, useState } from "react";
import {
    ArrowLeft, ArrowRight, CalendarDays, CheckCircle2, Clock3, DollarSign,
    Edit3, FileText, History, MessageSquare, RefreshCw, Save,
    ShieldCheck, Target, Users, XCircle, Zap, UserRound, FlaskConical, Download,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import StakeholderForm from "../components/StakeholderForm";
import PocForm from "../components/PocForm";
import {
    getPocsByOpportunity, getPoc, requestPoc, startPocExecution, submitPocResult, completePoc, downloadPoc
} from "../api/pocApi";
import { getStakeholdersByOpportunity } from "../api/stakeholderApi";
import {
    getOpportunity, getOpportunityStageHistory, getOpportunityValueHistory, changeOpportunityValue, updateOpportunity,
    submitOpportunityForReview, advanceToRfx, advanceToPoc, advanceToNegotiations,
    closeWon, closeLost, requestClosedWon, approveClosedWon, rejectClosedWon, markStalled, markActive
} from "../api/opportunityApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import { getUser } from "../auth/authStorage";
import Button from "../components/ui/Button";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import KpiCard from "../components/ui/KpiCard";
import StatusBadge from "../components/ui/StatusBadge";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";

const money = (value) => {
    if (value === null || value === undefined || value === "") return "—";
    const n = Number(value);
    if (Number.isNaN(n)) return String(value);
    if (Math.abs(n) >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (Math.abs(n) >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

const dateLabel = (value) =>
    value ? new Date(value).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "—";

function InfoGrid({ children }) {
    return <div className="opportunity-info-grid">{children}</div>;
}

function InfoItem({ label, value, icon: Icon }) {
    return (
        <div className="opportunity-info-item">
            <span>{Icon && <Icon size={13} />}{label}</span>
            <strong>{value || "—"}</strong>
        </div>
    );
}

function ActionNote({ children }) {
    return <span className="opportunity-action-note">{children}</span>;
}

export default function OpportunityDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const opportunityId = Number(id);
    const { activeRole } = useAuth();
    const currentUserId = Number(getUser()?.user_id);

    const [opportunity, setOpportunity] = useState(null);
    const [history, setHistory] = useState([]);
    const [valueHistory, setValueHistory] = useState([]);
    const [pocs, setPocs] = useState([]);
    const [stakeholders, setStakeholders] = useState([]);
    const [error, setError] = useState("");
    const [sectionErrors, setSectionErrors] = useState({
        history: null,
        valueHistory: null,
        stakeholders: null,
        pocs: null,
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [edit, setEdit] = useState(null);
    const [editingSales, setEditingSales] = useState(false);
    const [editingValue, setEditingValue] = useState(false);
    const [valueEdit, setValueEdit] = useState({ new_value: "", reason: "" });
    const [resultForms, setResultForms] = useState({});

    const technicalRole = activeRole === ROLES.SOLUTION_ENGINEER || activeRole === ROLES.PRE_SALES_MANAGER;
    const canLoadPocData = activeRole === ROLES.SOLUTION_ENGINEER || activeRole === ROLES.PRE_SALES_MANAGER;

    const describeSectionError = (err, fallback) => {
        const statusCode = err?.response?.status;
        const message = err?.response?.data?.message;

        if (statusCode === 403) {
            return {
                status: 403,
                message: message || "You do not have permission to view this section.",
            };
        }
        if (statusCode === 401) {
            return {
                status: 401,
                message: message || "Your session could not be authorized. Please sign in again if prompted.",
            };
        }
        if (statusCode >= 500 || !err?.response) {
            return {
                status: statusCode || "network",
                message: message || fallback,
            };
        }
        return {
            status: statusCode || "error",
            message: message || fallback,
        };
    };

    const setSectionError = (section, value) => {
        setSectionErrors((current) => ({ ...current, [section]: value }));
    };

    const loadOptionalSections = async () => {
        const requests = {
            history: getOpportunityStageHistory(opportunityId),
            valueHistory: getOpportunityValueHistory(opportunityId),
            stakeholders: getStakeholdersByOpportunity(opportunityId),
            ...(canLoadPocData ? { pocs: getPocsByOpportunity(opportunityId) } : {}),
        };

        const entries = Object.entries(requests);
        const results = await Promise.allSettled(entries.map(([, request]) => request));

        results.forEach((result, index) => {
            const [section] = entries[index];

            if (result.status === "fulfilled") {
                setSectionError(section, null);

                if (section === "history") {
                    setHistory(Array.isArray(result.value) ? result.value : []);
                } else if (section === "valueHistory") {
                    setValueHistory(Array.isArray(result.value) ? result.value : []);
                } else if (section === "stakeholders") {
                    setStakeholders(Array.isArray(result.value) ? result.value : []);
                } else if (section === "pocs") {
                    setPocs(Array.isArray(result.value) ? result.value : []);
                }
                return;
            }

            const err = result.reason;

            // An absent POC is also a valid empty state. The backend normally returns
            // an empty list, but keep a 404 non-fatal if an older backend does so.
            if (section === "pocs" && err?.response?.status === 404) {
                setPocs([]);
                setSectionError("pocs", null);
                return;
            }

            setSectionError(section, describeSectionError(
                err,
                `Unable to load ${section === "pocs" ? "POCs" : section === "stakeholders" ? "stakeholders" : section === "valueHistory" ? "value history" : "stage history"}.`
            ));
        });
    };

    const load = async () => {
        if (Number.isNaN(opportunityId)) {
            setError("Invalid opportunity ID.");
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            setError("");
            setSectionErrors({
                history: null,
                valueHistory: null,
                stakeholders: null,
                pocs: null,
                    });

            // The opportunity itself is the only page-critical request.
            const data = await getOpportunity(opportunityId);
            setOpportunity(data);
            setEdit({
                opportunity_name: data.opportunity_name || "",
                description: data.description || "",
                pain_points: data.pain_points || "",
                probability: data.probability ?? 0,
                expected_close_date: data.expected_close_date || "",
            });

            // Secondary data is intentionally isolated from the page-critical
            // opportunity request. One failed section must not blank the page.
            await loadOptionalSections();
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load this opportunity. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const retrySection = async (section) => {
        const requests = {
            history: getOpportunityStageHistory(opportunityId),
            valueHistory: getOpportunityValueHistory(opportunityId),
            stakeholders: getStakeholdersByOpportunity(opportunityId),
            pocs: getPocsByOpportunity(opportunityId),
        };

        if (section === "pocs" && !canLoadPocData) return;
        setSectionError(section, null);

        try {
            const value = await requests[section];
            if (section === "history") setHistory(Array.isArray(value) ? value : []);
            if (section === "valueHistory") setValueHistory(Array.isArray(value) ? value : []);
            if (section === "stakeholders") setStakeholders(Array.isArray(value) ? value : []);
            if (section === "pocs") setPocs(Array.isArray(value) ? value : []);
        } catch (err) {
            if (section === "pocs" && err?.response?.status === 404) {
                setPocs([]);
                return;
            }
            setSectionError(section, describeSectionError(
                err,
                `Unable to load ${section === "pocs" ? "POCs" : section === "stakeholders" ? "stakeholders" : section === "valueHistory" ? "value history" : "stage history"}.`
            ));
        }
    };

    useEffect(() => {
        load();
    }, [opportunityId, activeRole]);

    const assignedSE = opportunity?.team_members?.some(
        (member) => member.role === ROLES.SOLUTION_ENGINEER && member.user_id === currentUserId
    );

    const stageName = opportunity?.lifecycle_stage || "—";
    const status = opportunity?.operational_status || "—";
    const probability = Number(opportunity?.probability || 0);
    const outcome = opportunity?.outcome || "Open";
    const isClosed = status === "Closed";

    const canChangeValue =
        [ROLES.SALES_MANAGER, ROLES.PRE_SALES_MANAGER, ROLES.LEADERSHIP].includes(activeRole) &&
        opportunity?.operational_status !== "Closed";

    const canEditSales =
        activeRole === ROLES.SALES_EXECUTIVE &&
        opportunity?.created_by === currentUserId &&
        opportunity?.operational_status === "Active" &&
        stageName === "Lead" &&
        ["Draft", "Rejected"].includes(opportunity?.review_status);

    const canSubmitLead =
        [ROLES.SALES_EXECUTIVE, ROLES.SALES_MANAGER, ROLES.LEADERSHIP].includes(activeRole) &&
        opportunity?.created_by === currentUserId &&
        opportunity?.operational_status === "Active" &&
        opportunity?.outcome === "Open" &&
        stageName === "Lead" &&
        ["Draft", "Rejected"].includes(opportunity?.review_status);


    const run = async (fn) => {
        try {
            setSaving(true);
            setError("");
            await fn();
            await load();
        } catch (err) {
            if (err?.response?.status === 409) {
                setError("This opportunity changed before your action completed. Refreshing the latest state…");
                await load();
            } else {
                setError(err?.response?.data?.message || err?.message || "Action failed. Please try again.");
            }
        } finally {
            setSaving(false);
        }
    };

    const saveSales = () => run(async () => {
        await updateOpportunity(opportunityId, {
            ...edit,
            probability: Number(edit.probability || 0),
            expected_close_date: edit.expected_close_date || null,
            expected_version: opportunity.row_version,
        });
        setEditingSales(false);
    });

    const saveValue = () => run(async () => {
        await changeOpportunityValue(opportunityId, {
            new_value: valueEdit.new_value,
            reason: valueEdit.reason,
            expected_version: opportunity.row_version,
        });
        setEditingValue(false);
        setValueEdit({ new_value: "", reason: "" });
    });

    const submitPocRequest = async (payload) => {
        try {
            setSaving(true);
            setError("");
            await requestPoc({ ...payload, opportunity_id: opportunityId });
            await load();
        } catch (err) {
            const message = err?.response?.data?.message || err?.message || "Unable to create the POC. Please try again.";
            setError(message);
            throw err;
        } finally {
            setSaving(false);
        }
    };

    const close = (won) => {
        if (won) {
            return run(() => closeWon(opportunityId, { expected_version: opportunity.row_version }));
        }
        const reason = window.prompt("Closed Lost reason");
        if (!reason?.trim()) return;
        let explanation = "";
        if (reason.trim().toLowerCase() === "other") {
            explanation = window.prompt("Explain the Closed Lost reason (required for Other)") || "";
            if (!explanation.trim()) return;
        }
        return run(() => closeLost(opportunityId, {
            reason: reason.trim(),
            explanation: explanation.trim() || undefined,
            expected_version: opportunity.row_version
        }));
    };

    const requestWon = () => run(() => requestClosedWon(opportunityId, {
        expected_version: opportunity.row_version
    }));

    const resolveWonRequest = (approve) => {
        const reason = approve ? "" : (window.prompt("Reason for rejecting the Closed Won request") || "");
        if (!approve && !reason.trim()) return;
        const fn = approve ? approveClosedWon : rejectClosedWon;
        return run(() => fn(opportunityId, {
            expected_version: opportunity.row_version,
            reason: reason.trim() || undefined
        }));
    };

    const stageSteps = ["Lead", "Qualified", "RFX", "POC", "Negotiations", "Delivery"];
    const currentStageIndex = stageSteps.indexOf(stageName);

    const salesOwner = opportunity?.sales_owner?.full_name || "Pending assignment";
    const createdBy = opportunity?.created_by_user?.full_name || "Not recorded";
    const seMembers = (opportunity?.team_members || []).filter(
        (member) => member.role === ROLES.SOLUTION_ENGINEER
    );

    const teamMembers = useMemo(() => {
        const members = [];
        if (opportunity?.sales_owner) members.push({ key: `sales-${opportunity.sales_owner.user_id}`, label: "Sales Owner", name: opportunity.sales_owner.full_name });
        if (opportunity?.created_by_user && opportunity.created_by_user.user_id !== opportunity.sales_owner?.user_id) {
            members.push({ key: `creator-${opportunity.created_by_user.user_id}`, label: "Created By", name: opportunity.created_by_user.full_name });
        }
        seMembers.forEach((member) => members.push({
            key: `se-${member.team_id}`,
            label: "Solution Engineer",
            name: member.user?.full_name || `User #${member.user_id}`
        }));
        return members;
    }, [opportunity, seMembers]);

    if (loading && !opportunity) {
        return <div className="standard-page"><LoadingState message="Loading opportunity…" /></div>;
    }

    if (error && !opportunity) {
        return (
            <div className="standard-page">
                <PageHeader title="Opportunity Detail" description="Unable to load the requested opportunity." />
                <ErrorState message={error} onRetry={load} />
            </div>
        );
    }

    if (!opportunity) return null;

    return (
        <div className="standard-page opportunity-detail-page fade-in">
            <PageHeader
                title={opportunity.opportunity_name}
                description={`Opportunity #${opportunityId} · ${opportunity.account_name || `Account #${opportunity.account_id}`}`}
                actions={
                    <>
                        <Button variant="secondary" onClick={() => navigate(-1)}><ArrowLeft size={14} /> Back</Button>
                        <Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={14} /> Refresh</Button>
                    </>
                }
            />

            {error && <ErrorState message={error} onRetry={load} />}

            {isClosed && (
                <SectionCard title="Opportunity Locked" description="This opportunity is closed. Lifecycle, value, ownership, stakeholders, and closure fields are immutable." icon={History}>
                    <div className="opportunity-stage-summary">
                        <div><span>Final revenue</span><strong>{money(opportunity.final_revenue)}</strong></div>
                        <div><span>Outcome</span><strong>{outcome}</strong></div>
                    </div>
                </SectionCard>
            )}

            <SectionCard className="opportunity-hero-card">
                <div className="opportunity-hero-heading">
                    <div>
                        <span className="opportunity-eyebrow">Opportunity #{opportunityId}</span>
                        <h2>{opportunity.opportunity_name}</h2>
                        <p>{opportunity.account_name || `Account #${opportunity.account_id}`}</p>
                    </div>
                    <div className="opportunity-badge-stack">
                        <StatusBadge status={status} />
                        <StatusBadge status={stageName} />
                        <StatusBadge status={outcome} />
                    </div>
                </div>
            </SectionCard>

            <div className="ui-kpi-grid opportunity-summary-grid">
                <KpiCard icon={DollarSign} label="Estimated Value" value={money(opportunity.estimated_value)} description="Commercial value" />
                <KpiCard icon={Target} label="Probability" value={`${probability}%`} description="Current win probability" />
                <KpiCard icon={CalendarDays} label="Expected Close" value={dateLabel(opportunity.expected_close_date)} description="Target close date" />
                <KpiCard icon={Layers3Icon} label="Stage" value={stageName} description={status} />
            </div>

            {canChangeValue && (
                <SectionCard title="Opportunity Value" description="Commercial value changes require a reason and use optimistic concurrency." icon={DollarSign}>
                    {editingValue ? (
                        <div className="field-grid">
                            <label className="field-label"><span>New value</span><input type="number" min="0" step="0.01" value={valueEdit.new_value} onChange={(e) => setValueEdit({ ...valueEdit, new_value: e.target.value })} /></label>
                            <label className="field-label opportunity-field-full"><span>Reason</span><textarea rows="3" value={valueEdit.reason} onChange={(e) => setValueEdit({ ...valueEdit, reason: e.target.value })} placeholder="Why is the opportunity value changing?" /></label>
                            <div className="opportunity-form-actions opportunity-field-full"><Button variant="secondary" onClick={() => setEditingValue(false)}>Cancel</Button><Button disabled={saving || !valueEdit.reason.trim() || valueEdit.new_value === ""} onClick={saveValue}><Save size={14} /> Save value</Button></div>
                        </div>
                    ) : (
                        <div className="opportunity-stage-summary"><div><span>Current value</span><strong>{money(opportunity.estimated_value)}</strong></div><div><span>Version</span><strong>{opportunity.row_version}</strong></div><Button variant="secondary" onClick={() => { setValueEdit({ new_value: opportunity.estimated_value ?? "", reason: "" }); setEditingValue(true); }}><Edit3 size={13} /> Edit value</Button></div>
                    )}
                </SectionCard>
            )}

            <div className="opportunity-two-column">
                <SectionCard
                    title="Deal Overview"
                    description="Commercial context and opportunity metadata."
                    icon={FileText}
                    action={canEditSales && <Button variant="ghost" size="sm" onClick={() => setEditingSales((value) => !value)}><Edit3 size={13} />{editingSales ? "Cancel" : "Edit"}</Button>}
                >
                    {editingSales ? (
                        <div className="field-grid">
                            <label className="field-label"><span>Opportunity name</span><input value={edit.opportunity_name} onChange={(e) => setEdit({ ...edit, opportunity_name: e.target.value })} /></label>
                            <label className="field-label"><span>Expected close</span><input type="date" value={edit.expected_close_date} onChange={(e) => setEdit({ ...edit, expected_close_date: e.target.value })} /></label>
                            <label className="field-label"><span>Probability</span><input type="number" min="0" max="100" value={edit.probability} onChange={(e) => setEdit({ ...edit, probability: e.target.value })} /></label>
                            <label className="field-label opportunity-field-full"><span>Description</span><textarea rows="5" value={edit.description} onChange={(e) => setEdit({ ...edit, description: e.target.value })} /></label>
                            <label className="field-label opportunity-field-full"><span>Pain points</span><textarea rows="4" value={edit.pain_points} onChange={(e) => setEdit({ ...edit, pain_points: e.target.value })} /></label>
                            <div className="opportunity-form-actions opportunity-field-full"><Button disabled={saving} onClick={saveSales}><Save size={14} /> Save changes</Button></div>
                        </div>
                    ) : (
                        <>
                            <InfoGrid>
                                <InfoItem icon={DollarSign} label="Estimated value" value={money(opportunity.estimated_value)} />
                                <InfoItem icon={DollarSign} label="Final revenue" value={money(opportunity.final_revenue)} />
                                <InfoItem icon={Target} label="Probability" value={`${probability}%`} />
                                <InfoItem icon={CalendarDays} label="Expected close" value={dateLabel(opportunity.expected_close_date)} />
                                <InfoItem icon={Users} label="Sales owner" value={salesOwner} />
                            </InfoGrid>
                            <div className="opportunity-description">
                                <span>Description</span>
                                <p>{opportunity.description || "No description provided."}</p>
                            </div>
                        </>
                    )}
                </SectionCard>

                <SectionCard title="Ownership & Team" description="People currently associated with the opportunity." icon={Users}>
                    <div className="opportunity-team-list">
                        {teamMembers.length ? teamMembers.map((member) => (
                            <div className="opportunity-team-member" key={member.key}>
                                <span className="opportunity-avatar">{member.name?.charAt(0)?.toUpperCase() || "?"}</span>
                                <div><small>{member.label}</small><strong>{member.name}</strong></div>
                            </div>
                        )) : <EmptyState message="No team members are recorded." />}
                    </div>
                </SectionCard>
            </div>

            <SectionCard title="Opportunity Value History" description="Immutable record of every recorded Opportunity Value change." icon={History}>
                {sectionErrors.valueHistory ? (
                    <ErrorState title="Unable to load value history" message={sectionErrors.valueHistory.message} onRetry={() => retrySection("valueHistory")} />
                ) : valueHistory.length ? (
                    <div className="opportunity-history">
                        {valueHistory.map((entry) => (
                            <div className="opportunity-history-row" key={entry.history_id}>
                                <span className="opportunity-history-dot" />
                                <div>
                                    <strong>{money(entry.old_value)} → {money(entry.new_value)}</strong>
                                    <p>{entry.reason}</p>
                                    <small>{entry.actor?.full_name || `User #${entry.actor_id}`} · {entry.actor_active_role} · {dateLabel(entry.changed_at)} · v{entry.opportunity_row_version}</small>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : <EmptyState message="No value history is recorded for this opportunity." />}
            </SectionCard>

            <SectionCard title="Stage & Progression" description="Current stage and recorded stage history." icon={History}>
                <div className="opportunity-stage-summary">
                    <div>
                        <span>Current stage</span>
                        <strong>{stageName}</strong>
                    </div>
                    <div>
                        <span>Status</span>
                        <StatusBadge status={status} />
                    </div>
                    <div>
                        <span>Lifecycle</span>
                        <strong>{opportunity.lifecycle_stage || "—"}</strong>
                    </div>
                </div>
                {currentStageIndex >= 0 && (
                    <div className="opportunity-stage-rail">
                        {stageSteps.map((stage, index) => (
                            <div className={index === currentStageIndex ? "is-current" : index < currentStageIndex ? "is-done" : ""} key={stage}>
                                <span>{index + 1}</span><small>{stage}</small>
                            </div>
                        ))}
                    </div>
                )}
                {sectionErrors.history ? (
                    <ErrorState
                        title="Unable to load stage history"
                        message={sectionErrors.history.message}
                        onRetry={() => retrySection("history")}
                    />
                ) : history.length ? (
                    <div className="opportunity-history">
                        {history.map((entry, index) => (
                            <div className="opportunity-history-row" key={entry.history_id || index}>
                                <span className="opportunity-history-dot" />
                                <div>
                                    <strong>{entry.to_lifecycle_stage || entry.stage?.stage_name || `Stage #${entry.stage_id}`}</strong>
                                    <span>{dateLabel(entry.created_at)} · {entry.user?.full_name || "System"}{entry.remarks ? ` · ${entry.remarks}` : ""}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : <EmptyState message="No stage history recorded." />}
            </SectionCard>

            {canSubmitLead && (
                <SectionCard title="Sales Actions" description="Commercial actions available for this opportunity." icon={Zap}>
                    <div className="opportunity-action-row">
                        <Button disabled={saving} onClick={() => run(() => submitOpportunityForReview(opportunityId, opportunity.row_version))}><ShieldCheck size={14} /> Submit Lead for Sales Manager Review</Button>
                    </div>
                </SectionCard>
            )}

            {(activeRole === ROLES.SOLUTION_ENGINEER || activeRole === ROLES.PRE_SALES_MANAGER || activeRole === ROLES.LEADERSHIP) && opportunity.operational_status !== "Closed" && (
                <SectionCard title="Lifecycle Progress" description="Server-authorized lifecycle and closure actions." icon={Zap}>
                    <div className="opportunity-action-row">
                        {stageName === "Qualified" && <Button disabled={saving} onClick={() => run(() => advanceToRfx(opportunityId, opportunity.row_version))}><ArrowRight size={14} /> Advance to RFX</Button>}
                        {stageName === "RFX" && <Button disabled={saving} onClick={() => run(() => advanceToPoc(opportunityId, opportunity.row_version))}><ArrowRight size={14} /> Advance to POC</Button>}
                        {stageName === "POC" && <Button disabled={saving} onClick={() => run(() => advanceToNegotiations(opportunityId, opportunity.row_version))}><ArrowRight size={14} /> Advance to Negotiations</Button>}
                        {stageName !== "Lead" && (activeRole === ROLES.PRE_SALES_MANAGER || activeRole === ROLES.LEADERSHIP) && <Button disabled={saving} onClick={() => close(true)}><CheckCircle2 size={14} /> Close Won</Button>}
                        {stageName !== "Lead" && (activeRole === ROLES.PRE_SALES_MANAGER || activeRole === ROLES.LEADERSHIP || (activeRole === ROLES.SOLUTION_ENGINEER && assignedSE)) && <Button variant="secondary" disabled={saving} onClick={() => close(false)}><CheckCircle2 size={14} /> Close Lost</Button>}
                        {stageName !== "Lead" && activeRole === ROLES.SOLUTION_ENGINEER && opportunity?.closed_won_request?.status !== "Pending" && <Button variant="secondary" disabled={saving} onClick={requestWon}><CheckCircle2 size={14} /> Request Closed Won</Button>}
                        {opportunity?.closed_won_request?.status === "Pending" && activeRole === ROLES.PRE_SALES_MANAGER && (
                            <>
                                <Button disabled={saving} onClick={() => resolveWonRequest(true)}><CheckCircle2 size={14} /> Approve Closed Won</Button>
                                <Button variant="secondary" disabled={saving} onClick={() => resolveWonRequest(false)}>Reject Closed Won</Button>
                            </>
                        )}
                        {activeRole !== ROLES.SOLUTION_ENGINEER || assignedSE ? null : <ActionNote>This role is not assigned to this opportunity.</ActionNote>}
                    </div>
                </SectionCard>
            )}

            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && opportunity.is_active && stageName === "POC" && (
                <SectionCard title="Create POC" description="Define the technical proof of concept for this opportunity." icon={FlaskConical}>
                    <PocForm
                        fixedOpportunity={opportunity}
                        onSubmit={submitPocRequest}
                        submitting={saving}
                    />
                </SectionCard>
            )}

            {technicalRole && (
                    <SectionCard title="POC Execution" description="POCs associated with this opportunity. Manager approval is not part of the lifecycle." icon={FlaskConical}>
                        {sectionErrors.pocs ? (
                            <ErrorState
                                title={sectionErrors.pocs.status === 403 ? "POC data is read-only" : "Unable to load POCs"}
                                message={sectionErrors.pocs.message}
                                onRetry={sectionErrors.pocs.status === 403 ? undefined : () => retrySection("pocs")}
                            />
                        ) : pocs.length ? (
                            <div className="opportunity-poc-list">
                                {pocs.map((poc) => {
                                    const form = resultForms[poc.poc_id] || {
                                        
                                        outcome: poc.outcome || "Success",
                                        outcome_notes: poc.outcome_notes || "",
                                        remarks: poc.remarks || ""
                                    };
                                    return (
                                        <article className="opportunity-poc-card" key={poc.poc_id}>
                                            <div className="opportunity-poc-heading">
                                                <div><strong>{poc.poc_name}</strong><span>{poc.objective || "No objective provided."}</span></div>
                                                <StatusBadge status={poc.status} />
                                            </div>
                                            <div className="opportunity-poc-meta">
                                                <span><Target size={12} />{poc.success_metric || "No success criteria"}</span>
                                                <span><CalendarDays size={12} />{dateLabel(poc.target_date)}</span>
                                                <span><Clock3 size={12} />{poc.outcome || "Not completed"}</span>
                                            </div>
                                            <div className="opportunity-detail-text-grid">
                                                <div><span>Exit criteria</span><p>{poc.exit_criteria || "—"}</p></div>
                                                <div><span>Failure condition</span><p>{poc.failure_condition || "—"}</p></div>
                                                <div><span>Outcome notes</span><p>{poc.outcome_notes || "—"}</p></div>
                                            </div>
                                            
                                          {activeRole === ROLES.SOLUTION_ENGINEER &&
    assignedSE &&
    poc.status === "Draft" && (
        <Button
            size="sm"
            disabled={saving}
            onClick={() =>
                run(() =>
                    startPocExecution(
                        poc.poc_id,
                        { updated_at: poc.updated_at }
                    )
                )
            }
        >
            <Zap size={13} /> Start POC
        </Button>
    )}

{activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && (
    <Button
        size="sm"
        disabled={saving}
        onClick={() => run(() => downloadPoc(poc.poc_id))}
    >
        <Download size={13} /> Download POC
    </Button>
)}
                                            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && poc.status === "In Progress" && (
                                                <div className="opportunity-poc-result">
                                                    
                                                    <select value={form.outcome} onChange={(e) => setResultForms({ ...resultForms, [poc.poc_id]: { ...form, outcome: e.target.value } })}>
                                                        {["Success", "Failure", "Ongoing", "Abandoned"].map((value) => <option key={value}>{value}</option>)}
                                                    </select>
                                                    <textarea placeholder="Outcome notes" value={form.outcome_notes} onChange={(e) => setResultForms({ ...resultForms, [poc.poc_id]: { ...form, outcome_notes: e.target.value } })} />
                                                    <textarea placeholder="Execution remarks" value={form.remarks} onChange={(e) => setResultForms({ ...resultForms, [poc.poc_id]: { ...form, remarks: e.target.value } })} />
                                                    <Button disabled={saving} onClick={() => run(async () => {
    const latest = await getPoc(poc.poc_id);
    await submitPocResult(poc.poc_id, {
        outcome: form.outcome,
        outcome_notes: form.outcome_notes,
        remarks: form.remarks,
        execution_status: "Submitted",
        updated_at: latest.updated_at,
    });
})}><MessageSquare size={13} /> Submit result</Button>
                                                </div>
                                            )}
                                            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && poc.status === "Submitted" && (
                                                <Button size="sm" disabled={saving} onClick={() => run(() => completePoc(poc.poc_id, { updated_at: poc.updated_at }))}><CheckCircle2 size={13} /> Complete POC</Button>
                                            )}
                                        </article>
                                    );
                                })}
                            </div>
                        ) : <EmptyState message="No POCs have been created for this opportunity." />}
                    </SectionCard>
            )}


            <SectionCard title="Stakeholders" description="Customer contacts connected to this opportunity." icon={Users}>
                {((activeRole === ROLES.SALES_EXECUTIVE &&
                    opportunity.created_by === currentUserId &&
                    opportunity.is_active &&
                    opportunity.operational_status === "Active" &&
                    stageName === "Lead" &&
                    ["Draft", "Rejected"].includes(opportunity.review_status)) ||
                    (activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && opportunity.is_active)) && (
                    <StakeholderForm opportunityId={opportunityId} onCreated={() => retrySection("stakeholders")} />
                )}
                {sectionErrors.stakeholders ? (
                    <ErrorState
                        title={sectionErrors.stakeholders.status === 403 ? "Stakeholders are read-only" : "Unable to load stakeholders"}
                        message={sectionErrors.stakeholders.message}
                        onRetry={sectionErrors.stakeholders.status === 403 ? undefined : () => retrySection("stakeholders")}
                    />
                ) : stakeholders.length ? (
                    <div className="opportunity-stakeholder-list">
                        {stakeholders.map((stakeholder) => (
                            <div className="opportunity-stakeholder" key={stakeholder.stakeholder_id}>
                                <span className="opportunity-avatar">{(stakeholder.stakeholder_name || "?").charAt(0).toUpperCase()}</span>
                                <div>
                                    <strong>{stakeholder.stakeholder_name || "Unnamed stakeholder"}</strong>
                                    <small>{stakeholder.designation || "Role not provided"}</small>
                                </div>
                                <div className="opportunity-stakeholder-contact">
                                    {stakeholder.email && <span><UserRound size={12} />{stakeholder.email}</span>}
                                    {stakeholder.phone && <span><PhoneIcon size={12} />{stakeholder.phone}</span>}
                                    {stakeholder.influence_level && <StatusBadge status={stakeholder.influence_level} />}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : <EmptyState message="No stakeholders recorded." />}
            </SectionCard>
        </div>
    );
}

function Layers3Icon(props) {
    return <span {...props}>▱</span>;
}

function PhoneIcon({ size = 12 }) {
    return <span style={{ fontSize: size }}>☎</span>;
}
