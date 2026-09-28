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
    requestPoc
} from "../api/pocApi";
import {
    getPocsV2ByOpportunity,
    getPocHistoryV2,
    getPocTeamCandidates,
    assignPocTeam,
    submitPocV2,
    completePocV2,
    requestNewPocV2
} from "../api/phase2Api";
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
import Phase2OpportunityPanel from "../components/Phase2OpportunityPanel";

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
    const [pocHistory, setPocHistory] = useState([]);
    const [pocs, setPocs] = useState([]);
    const [stakeholders, setStakeholders] = useState([]);
    const [error, setError] = useState("");
    const [sectionErrors, setSectionErrors] = useState({
        history: null,
        valueHistory: null,
        pocHistory: null,
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
    const [pocCandidates, setPocCandidates] = useState([]);
    const [pocTeamSelections, setPocTeamSelections] = useState({});
    const [pocResultLinks, setPocResultLinks] = useState({});
    const [pocOutcomes, setPocOutcomes] = useState({});
    const [pocRepeatReasons, setPocRepeatReasons] = useState({});
    const [pocRepeatSaving, setPocRepeatSaving] = useState({});

    const pocRoles = [
        ROLES.SOLUTION_ENGINEER,
        ROLES.PRE_SALES_MANAGER,
        ROLES.DELIVERY_MANAGER,
        ROLES.LEADERSHIP,
        ROLES.DEVOPS_ENGINEER,
        ROLES.DATA_ANALYST,
    ];
    const technicalRole = pocRoles.includes(activeRole);
    const canLoadPocData = pocRoles.includes(activeRole);
    const canAssignPocTeam = [ROLES.DELIVERY_MANAGER, ROLES.LEADERSHIP].includes(activeRole);

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
            pocHistory: getPocHistoryV2(opportunityId),
            stakeholders: getStakeholdersByOpportunity(opportunityId),
            ...(canLoadPocData ? { pocs: getPocsV2ByOpportunity(opportunityId) } : {}),
            ...(canAssignPocTeam ? { pocCandidates: getPocTeamCandidates() } : {}),
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
                } else if (section === "pocHistory") {
                    setPocHistory(Array.isArray(result.value) ? result.value : []);
                } else if (section === "stakeholders") {
                    setStakeholders(Array.isArray(result.value) ? result.value : []);
                } else if (section === "pocs") {
                    setPocs(Array.isArray(result.value) ? result.value : []);
                } else if (section === "pocCandidates") {
                    setPocCandidates(Array.isArray(result.value) ? result.value : []);
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
                `Unable to load ${section === "pocs" ? "POCs" : section === "stakeholders" ? "stakeholders" : section === "valueHistory" ? "value history" : section === "pocHistory" ? "POC history" : "stage history"}.`
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
                pocHistory: null,
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
            pocHistory: getPocHistoryV2(opportunityId),
            stakeholders: getStakeholdersByOpportunity(opportunityId),
            pocs: getPocsV2ByOpportunity(opportunityId),
        };

        if (section === "pocs" && !canLoadPocData) return;
        setSectionError(section, null);

        try {
            const value = await requests[section];
            if (section === "history") setHistory(Array.isArray(value) ? value : []);
            if (section === "valueHistory") setValueHistory(Array.isArray(value) ? value : []);
            if (section === "pocHistory") setPocHistory(Array.isArray(value) ? value : []);
            if (section === "stakeholders") setStakeholders(Array.isArray(value) ? value : []);
            if (section === "pocs") setPocs(Array.isArray(value) ? value : []);
        } catch (err) {
            if (section === "pocs" && err?.response?.status === 404) {
                setPocs([]);
                return;
            }
            setSectionError(section, describeSectionError(
                err,
                `Unable to load ${section === "pocs" ? "POCs" : section === "stakeholders" ? "stakeholders" : section === "valueHistory" ? "value history" : section === "pocHistory" ? "POC history" : "stage history"}.`
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
        [ROLES.LEADERSHIP, ROLES.SALES_MANAGER, ROLES.SALES_EXECUTIVE, ROLES.PRE_SALES_MANAGER, ROLES.SOLUTION_ENGINEER, ROLES.DELIVERY_MANAGER, ROLES.DEVOPS_ENGINEER, ROLES.DATA_ANALYST].includes(activeRole) &&
        opportunity?.created_by === currentUserId &&
        opportunity?.operational_status === "Active" &&
        stageName === "Lead" &&
        opportunity?.review_status === "Draft";

    const canSubmitLead =
        [ROLES.LEADERSHIP, ROLES.SALES_MANAGER, ROLES.SALES_EXECUTIVE, ROLES.PRE_SALES_MANAGER, ROLES.SOLUTION_ENGINEER, ROLES.DELIVERY_MANAGER, ROLES.DEVOPS_ENGINEER, ROLES.DATA_ANALYST].includes(activeRole) &&
        opportunity?.created_by === currentUserId &&
        opportunity?.operational_status === "Active" &&
        opportunity?.outcome === "Open" &&
        stageName === "Lead" &&
        opportunity?.review_status === "Draft";


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

    const requestNewPoc = async (poc) => {
        const reason = (pocRepeatReasons[poc.poc_id] || "").trim();

        if (!reason) {
            setError("A reason is required to request a new POC.");
            return;
        }

        try {
            setPocRepeatSaving((current) => ({
                ...current,
                [poc.poc_id]: true,
            }));
            setError("");

            await requestNewPocV2(opportunityId, {
                reason,
                row_version: poc.row_version,
            });

            setPocRepeatReasons((current) => ({
                ...current,
                [poc.poc_id]: "",
            }));

            await retrySection("pocs");
        } catch (err) {
            if (err?.response?.status === 409) {
                setError(
                    "This POC changed before your request completed. Refreshing the latest POC state…"
                );
                await retrySection("pocs");
            } else {
                setError(
                    err?.response?.data?.message ||
                    err?.message ||
                    "Unable to request a new POC. Please try again."
                );
            }
        } finally {
            setPocRepeatSaving((current) => ({
                ...current,
                [poc.poc_id]: false,
            }));
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
                        {outcome === "Closed Lost" && opportunity.lost_explanation && <div><span>Closed Lost Remark</span><strong>{opportunity.lost_explanation}</strong></div>}
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
                <KpiCard icon={DollarSign} label="Current Opportunity Value" value={money(opportunity.estimated_value)} description="Commercial value" />
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
                                <InfoItem icon={DollarSign} label="Current Opportunity Value" value={money(opportunity.estimated_value)} />
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

            <SectionCard title="POC History" description="Timeline of POC starts, result submissions, and repeat requests." icon={History}>
                {sectionErrors.pocHistory ? (
                    <ErrorState
                        title="Unable to load POC history"
                        message={sectionErrors.pocHistory.message}
                        onRetry={() => retrySection("pocHistory")}
                    />
                ) : pocHistory.length ? (
                    <div className="opportunity-history">
                        {pocHistory.map((entry) => (
                            <div className="opportunity-history-row" key={entry.history_id}>
                                <span className="opportunity-history-dot" />
                                <div>
                                    <strong>
                                        {{
                                            POC_STARTED: "POC started",
                                            POC_SUBMITTED: "POC result submitted",
                                            NEW_POC_REQUESTED: "New POC requested",
                                        }[entry.event_type] || (entry.event_type || "POC event").replaceAll("_", " ")}
                                    </strong>
                                    {entry.reason && <p>{entry.reason}</p>}
                                    <small>
                                        {entry.actor?.full_name || `User #${entry.actor_id}`}
                                        {" · "}{dateLabel(entry.created_at)}
                                    </small>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : <EmptyState message="No POC history is recorded for this opportunity." />}
            </SectionCard>

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
                        {stageName === "POC" && (
                            <Button
                                disabled={
                                    saving ||
                                    !pocs.some(
                                        (poc) =>
                                            poc.status === "Completed" &&
                                            poc.outcome === "Success"
                                    )
                                }
                                onClick={() =>
                                    run(() =>
                                        advanceToNegotiations(
                                            opportunityId,
                                            opportunity.row_version
                                        )
                                    )
                                }
                            >
                                <ArrowRight size={14} />
                                Advance to Negotiations
                            </Button>
                        )}
                        {stageName !== "Lead" && (activeRole === ROLES.PRE_SALES_MANAGER || activeRole === ROLES.LEADERSHIP) && <Button disabled={saving} onClick={() => close(true)}><CheckCircle2 size={14} /> {stageName === "Negotiations" ? "Final Closed Won Approval" : "Close Won"}</Button>}
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
                <SectionCard
                    title="POC Execution"
                    description="POC execution, team assignment, and result submission."
                    icon={FlaskConical}
                >
                    {sectionErrors.pocs ? (
                        <ErrorState
                            title={sectionErrors.pocs.status === 403 ? "POC data is read-only" : "Unable to load POCs"}
                            message={sectionErrors.pocs.message}
                            onRetry={sectionErrors.pocs.status === 403 ? undefined : () => retrySection("pocs")}
                        />
                    ) : pocs.length ? (
                        <div className="opportunity-poc-list">
                            {pocs.map((poc) => {
                                const team = Array.isArray(poc.team) ? poc.team : [];

                                const isAssignedPocMember = team.some(
                                    (member) =>
                                        Number(member.user_id) === Number(currentUserId) &&
                                        member.role === activeRole
                                );

                                const selectedMembers = pocTeamSelections[poc.poc_id] || [];

                                const resultLink = pocResultLinks[poc.poc_id] || "";

                                const canSubmitResult =
                                    [ROLES.DEVOPS_ENGINEER, ROLES.DATA_ANALYST].includes(activeRole) &&
                                    isAssignedPocMember &&
                                    ["Draft", "In Progress"].includes(poc.status);

                                const canCompletePoc =
                                    activeRole === ROLES.SOLUTION_ENGINEER &&
                                    assignedSE &&
                                    opportunity?.is_active &&
                                    opportunity?.operational_status === "Active" &&
                                    opportunity?.outcome === "Open" &&
                                    stageName === "POC" &&
                                    poc.status === "Submitted";

                                const toggleTeamMember = (userId) => {
                                    setPocTeamSelections((current) => {
                                        const existing = current[poc.poc_id] || [];
                                        const exists = existing.includes(userId);

                                        if (exists) {
                                            return {
                                                ...current,
                                                [poc.poc_id]: existing.filter((id) => id !== userId),
                                            };
                                        }

                                        if (existing.length >= 2) {
                                            return current;
                                        }

                                        return {
                                            ...current,
                                            [poc.poc_id]: [...existing, userId],
                                        };
                                    });
                                };

                                return (
                                    <article className="opportunity-poc-card" key={poc.poc_id}>
                                        <div className="opportunity-poc-heading">
                                            <div>
                                                <strong>{poc.poc_name}</strong>
                                                <span>POC #{poc.poc_id}</span>
                                            </div>
                                            <StatusBadge status={poc.status} />
                                        </div>

                                        <div className="opportunity-poc-meta">
                                            <span>
                                                <CalendarDays size={12} />
                                                Target date: {dateLabel(poc.target_date)}
                                            </span>
                                            <span>
                                                <Clock3 size={12} />
                                                Status: {poc.status || "—"}
                                            </span>
                                        </div>

                                        <div className="opportunity-detail-text-grid">
                                            <div>
                                                <span>Result / View Link</span>
                                                <p>
                                                    {poc.result_view_link ? (
                                                        <a
                                                            href={poc.result_view_link}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                        >
                                                            {poc.result_view_link}
                                                        </a>
                                                    ) : (
                                                        "Not submitted"
                                                    )}
                                                </p>
                                            </div>

                                            <div>
                                                <span>Submitted by</span>
                                                <p>{poc.submitted_by || "—"}</p>
                                            </div>

                                            <div>
                                                <span>Submitted at</span>
                                                <p>
                                                    {poc.submitted_at
                                                        ? new Date(poc.submitted_at).toLocaleString()
                                                        : "—"}
                                                </p>
                                            </div>

                                            <div>
                                                <span>Requested by</span>
                                                <p>{poc.requested_by || "—"}</p>
                                            </div>
                                        </div>

                                        <div style={{ marginTop: "12px" }}>
                                            <strong style={{ display: "block", marginBottom: "8px" }}>
                                                POC Team
                                            </strong>

                                            {team.length ? (
                                                <div style={{ display: "grid", gap: "6px" }}>
                                                    {team.map((member) => (
                                                        <div
                                                            key={`${poc.poc_id}-${member.user_id}`}
                                                            style={{
                                                                display: "flex",
                                                                justifyContent: "space-between",
                                                                alignItems: "center",
                                                                padding: "8px 10px",
                                                                border: "1px solid var(--border-color, #ddd)",
                                                                borderRadius: "6px",
                                                            }}
                                                        >
                                                            <span>
    {member.full_name ||
        pocCandidates.find(
            (candidate) => Number(candidate.user_id) === Number(member.user_id)
        )?.full_name ||
        `User #${member.user_id}`}
</span>
                                                            <StatusBadge status={member.role} />
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p>No POC team assigned yet.</p>
                                            )}
                                        </div>

                                        {poc.permission_disclaimer && (
                                            <div
                                                style={{
                                                    marginTop: "12px",
                                                    padding: "10px 12px",
                                                    borderRadius: "6px",
                                                    background: "var(--surface-muted, #f5f5f5)",
                                                    fontSize: "12px",
                                                }}
                                            >
                                                <ShieldCheck size={13} style={{ verticalAlign: "middle", marginRight: "6px" }} />
                                                {poc.permission_disclaimer}
                                            </div>
                                        )}

                                        {canAssignPocTeam && poc.status !== "Submitted" && (
                                            <div style={{ marginTop: "16px" }}>
                                                <strong style={{ display: "block", marginBottom: "8px" }}>
                                                    Assign POC Team
                                                </strong>

                                                {pocCandidates.length ? (
                                                    <div style={{ display: "grid", gap: "8px" }}>
                                                        {pocCandidates.map((candidate) => {
                                                            const selected = selectedMembers.includes(candidate.user_id);

                                                            return (
                                                                <label
                                                                    key={candidate.user_id}
                                                                    style={{
                                                                        display: "flex",
                                                                        alignItems: "center",
                                                                        gap: "8px",
                                                                        padding: "8px 10px",
                                                                        border: "1px solid var(--border-color, #ddd)",
                                                                        borderRadius: "6px",
                                                                        cursor: "pointer",
                                                                    }}
                                                                >
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={selected}
                                                                        onChange={() => toggleTeamMember(candidate.user_id)}
                                                                    />

                                                                    <span>
                                                                        <strong>{candidate.full_name}</strong>
                                                                        {candidate.email && (
                                                                            <small style={{ display: "block" }}>
                                                                                {candidate.email}
                                                                            </small>
                                                                        )}
                                                                    </span>

                                                                    <span style={{ marginLeft: "auto", fontSize: "12px" }}>
                                                                        {(candidate.roles || []).join(", ")}
                                                                    </span>
                                                                </label>
                                                            );
                                                        })}
                                                    </div>
                                                ) : (
                                                    <p>No eligible DevOps Engineer or Data Analyst users found.</p>
                                                )}

                                                <div style={{ marginTop: "10px" }}>
                                                    <Button
                                                        size="sm"
                                                        disabled={saving || selectedMembers.length === 0}
                                                        onClick={() =>
                                                            run(async () => {
                                                                await assignPocTeam(
                                                                    poc.poc_id,
                                                                    selectedMembers
                                                                );
                                                                setPocTeamSelections((current) => ({
                                                                    ...current,
                                                                    [poc.poc_id]: [],
                                                                }));
                                                                await retrySection("pocs");
                                                                await retrySection("pocHistory");
                                                            })
                                                        }
                                                    >
                                                        <Users size={13} />
                                                        Assign team ({selectedMembers.length}/2)
                                                    </Button>
                                                </div>
                                            </div>
                                        )}

                                        {canSubmitResult && (
                                            <div
                                                className="opportunity-poc-result"
                                                style={{ marginTop: "16px" }}
                                            >
                                                <strong>Submit POC Result</strong>

                                                <input
                                                    type="url"
                                                    placeholder="https://drive.google.com/..."
                                                    value={resultLink}
                                                    onChange={(e) =>
                                                        setPocResultLinks((current) => ({
                                                            ...current,
                                                            [poc.poc_id]: e.target.value,
                                                        }))
                                                    }
                                                />

                                                <Button
                                                    disabled={saving || !resultLink.trim()}
                                                    onClick={() =>
                                                        run(async () => {
                                                            await submitPocV2(poc.poc_id, {
                                                                result_view_link: resultLink.trim(),
                                                                row_version: poc.row_version,
                                                            });

                                                            setPocResultLinks((current) => ({
                                                                ...current,
                                                                [poc.poc_id]: "",
                                                            }));

                                                            await retrySection("pocs");

                                                            await retrySection("pocHistory");
                                                        })
                                                    }
                                                >
                                                    <MessageSquare size={13} />
                                                    Submit result
                                                </Button>
                                            </div>
                                        )}

                                        {poc.status === "Submitted" && (
                                            <div style={{ marginTop: "14px" }}>
                                                <StatusBadge status="Submitted" />
                                                <span style={{ marginLeft: "8px", fontSize: "12px" }}>
                                                    Result is submitted and immutable.
                                                </span>
                                            </div>
                                        )}

                                        {poc.status === "Completed" && poc.outcome && (
                                            <div
                                                style={{
                                                    marginTop: "10px",
                                                    fontSize: "12px",
                                                    fontWeight: 600,
                                                }}
                                            >
                                                Outcome: {poc.outcome}
                                            </div>
                                        )}

                                        {canCompletePoc && (
                                            <div
                                                style={{
                                                    marginTop: "16px",
                                                    paddingTop: "14px",
                                                    borderTop: "1px solid var(--border-color, #ddd)",
                                                }}
                                            >
                                                <strong style={{ display: "block", marginBottom: "8px" }}>
                                                    Complete POC
                                                </strong>

                                                <select
                                                    value={pocOutcomes[poc.poc_id] || ""}
                                                    onChange={(e) =>
                                                        setPocOutcomes((current) => ({
                                                            ...current,
                                                            [poc.poc_id]: e.target.value,
                                                        }))
                                                    }
                                                    disabled={saving}
                                                    style={{
                                                        width: "100%",
                                                        padding: "8px",
                                                        marginBottom: "8px",
                                                    }}
                                                >
                                                    <option value="">Select POC outcome</option>
                                                    <option value="Success">Success</option>
                                                    <option value="Failure">Failure</option>
                                                </select>

                                                <Button
                                                    disabled={saving || !pocOutcomes[poc.poc_id]}
                                                    onClick={() =>
                                                        run(async () => {
                                                            await completePocV2(poc.poc_id, {
                                                                outcome: pocOutcomes[poc.poc_id],
                                                            });

                                                            setPocOutcomes((current) => ({
                                                                ...current,
                                                                [poc.poc_id]: "",
                                                            }));

                                                            await retrySection("pocs");
                                                            await retrySection("pocHistory");
                                                            await retrySection("opportunity");
                                                        })
                                                    }
                                                >
                                                    <CheckCircle2 size={13} />
                                                    Complete POC
                                                </Button>
                                            </div>
                                        )}

                                        {activeRole === ROLES.SOLUTION_ENGINEER &&
                                            assignedSE &&
                                            opportunity?.is_active &&
                                            opportunity?.operational_status === "Active" &&
                                            opportunity?.outcome === "Open" &&
                                            stageName === "POC" &&
                                            poc.status === "Submitted" && (
                                                <div
                                                    style={{
                                                        marginTop: "16px",
                                                        paddingTop: "14px",
                                                        borderTop: "1px solid var(--border-color, #ddd)",
                                                    }}
                                                >
                                                    <strong style={{ display: "block", marginBottom: "6px" }}>
                                                        Request New POC
                                                    </strong>

                                                    <p
                                                        style={{
                                                            margin: "0 0 10px",
                                                            fontSize: "12px",
                                                            color: "var(--text-muted, #666)",
                                                        }}
                                                    >
                                                        Request another POC cycle using the existing POC team.
                                                        The submitted POC remains unchanged.
                                                    </p>

                                                    <textarea
                                                        rows={3}
                                                        placeholder="Enter the reason for requesting another POC..."
                                                        value={pocRepeatReasons[poc.poc_id] || ""}
                                                        onChange={(e) =>
                                                            setPocRepeatReasons((current) => ({
                                                                ...current,
                                                                [poc.poc_id]: e.target.value,
                                                            }))
                                                        }
                                                        disabled={Boolean(pocRepeatSaving[poc.poc_id])}
                                                        style={{
                                                            width: "100%",
                                                            boxSizing: "border-box",
                                                            resize: "vertical",
                                                            marginBottom: "10px",
                                                        }}
                                                    />

                                                    <Button
                                                        variant="secondary"
                                                        disabled={
                                                            Boolean(pocRepeatSaving[poc.poc_id]) ||
                                                            !(pocRepeatReasons[poc.poc_id] || "").trim()
                                                        }
                                                        onClick={() => requestNewPoc(poc)}
                                                    >
                                                        <RefreshCw size={13} />
                                                        {pocRepeatSaving[poc.poc_id]
                                                            ? "Requesting..."
                                                            : "Request new POC"}
                                                    </Button>
                                                </div>
                                            )}
                                    </article>
                                );
                            })}
                        </div>
                    ) : (
                        <EmptyState message="No POCs have been created for this opportunity." />
                    )}
                </SectionCard>
            )}

            <Phase2OpportunityPanel opportunity={opportunity} activeRole={activeRole} onRefresh={() => retrySection("stakeholders")} />

            <SectionCard title="Stakeholders" description="Customer contacts connected to this opportunity." icon={Users}>
                {(([ROLES.LEADERSHIP, ROLES.SALES_MANAGER, ROLES.SALES_EXECUTIVE, ROLES.PRE_SALES_MANAGER, ROLES.SOLUTION_ENGINEER, ROLES.DELIVERY_MANAGER, ROLES.DEVOPS_ENGINEER, ROLES.DATA_ANALYST].includes(activeRole) &&
                    opportunity.created_by === currentUserId &&
                    opportunity.is_active &&
                    opportunity.operational_status === "Active" &&
                    stageName === "Lead" &&
                    opportunity.review_status === "Draft") ||
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
                                <span className="opportunity-avatar">{(stakeholder.name || "?").charAt(0).toUpperCase()}</span>
                                <div>
                                    <strong>{stakeholder.name || "Unnamed stakeholder"}</strong>
                                    <small>{stakeholder.job_title || "Role not provided"}</small>
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
