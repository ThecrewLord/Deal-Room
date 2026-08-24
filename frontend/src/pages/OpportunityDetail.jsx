import { useEffect, useState } from "react";
import {
    ArrowLeft, ArrowRight, CalendarDays, CheckCircle2, Clock3, DollarSign,
    Edit3, FileText, History, Layers3, Link2, MessageSquare, Pencil,
    RefreshCw, Save, ShieldCheck, Target, Users, XCircle, Zap
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import StakeholderForm from "../components/StakeholderForm";
import {
    getPocsByOpportunity, requestPoc, startPocExecution, submitPocResult,
    completePoc
} from "../api/pocApi";
import { getStakeholdersByOpportunity } from "../api/stakeholderApi";
import {
    getOpportunity, getOpportunityStageHistory, updateOpportunity,
    qualifyOpportunity, submitOpportunityForReview, transitionTechnicalStage,
    closeWon, closeLost
} from "../api/opportunityApi";
import { getSolutionDesign, updateSolutionDesign } from "../api/solutionDesignApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import { getUser } from "../auth/authStorage";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import PageHeader from "../components/ui/PageHeader";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

const statusClass = (value = "") => `ui-status-badge ui-status-${value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
const dateLabel = (value) => value ? new Date(value).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "—";

function SectionHeader({ icon: Icon, title, description, action }) {
    return (
        <div className="opp-section-head">
            <div className="opp-section-title">
                <span className="opp-section-icon"><Icon size={16} /></span>
                <div><h2>{title}</h2>{description && <p>{description}</p>}</div>
            </div>
            {action}
        </div>
    );
}

function InfoItem({ label, value, icon: Icon }) {
    return <div className="opp-info-item"><span>{Icon && <Icon size={13} />}{label}</span><strong>{value || "—"}</strong></div>;
}

function Empty({ children }) {
    return <div className="opp-empty"><div className="opp-empty-icon"><Layers3 size={17} /></div><span>{children}</span></div>;
}

export default function OpportunityDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const opportunityId = Number(id);
    const { activeRole } = useAuth();
    const currentUserId = Number(getUser()?.user_id);

    const [opportunity, setOpportunity] = useState(null);
    const [history, setHistory] = useState([]);
    const [pocs, setPocs] = useState([]);
    const [design, setDesign] = useState(null);
    const [stakeholders, setStakeholders] = useState([]);
    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);
    const [edit, setEdit] = useState(null);
    const [editingSales, setEditingSales] = useState(false);
    const [designEdit, setDesignEdit] = useState(null);
    const [pocForm, setPocForm] = useState({
        poc_name: "", objective: "", success_metric: "", exit_criteria: "",
        target_date: "", failure_condition: "", remarks: ""
    });
    const [resultForms, setResultForms] = useState({});

    const load = async () => {
        try {
            setError("");
            const data = await getOpportunity(opportunityId);
            setOpportunity(data);
            setEdit({
                opportunity_name: data.opportunity_name || "",
                description: data.description || "",
                estimated_value: data.estimated_value ?? "",
                probability: data.probability ?? 0,
                expected_close_date: data.expected_close_date || "",
            });

            const technical = activeRole === ROLES.SOLUTION_ENGINEER;
            const [stageHistory, p, s, d] = await Promise.all([
                getOpportunityStageHistory(opportunityId).catch(() => []),
                getPocsByOpportunity(opportunityId).catch(() => []),
                getStakeholdersByOpportunity(opportunityId).catch(() => []),
                technical ? getSolutionDesign(opportunityId).catch(() => null) : Promise.resolve(null),
            ]);
            setHistory(stageHistory);
            setPocs(p);
            setStakeholders(s);
            setDesign(d);
            setDesignEdit(d || {
                solution_summary: "", technical_approach: "", technical_requirements: "",
                architecture_notes: "", risks: "", assumptions: ""
            });
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load opportunity.");
        }
    };

    useEffect(() => {
        if (!Number.isNaN(opportunityId)) load();
    }, [opportunityId, activeRole]);

    const assignedSE = opportunity?.team_members?.some(
        m => m.role === ROLES.SOLUTION_ENGINEER && m.user_id === currentUserId
    );

    const canEditSales =
        activeRole === ROLES.SALES_EXECUTIVE &&
        opportunity?.created_by === currentUserId &&
        opportunity?.status === "Open" &&
        opportunity?.is_active &&
        ["Lead / Identified", "Qualification"].includes(opportunity?.current_stage?.stage_name);

    const technicalStage = opportunity?.current_stage?.stage_name;
    const canEditDesign = activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && opportunity?.is_active;

    const run = async (fn) => {
        try {
            setSaving(true);
            setError("");
            await fn();
            await load();
        } catch (e) {
            setError(e?.response?.data?.message || e?.message || "Action failed.");
        } finally {
            setSaving(false);
        }
    };

    const saveSales = () => run(async () => {
        await updateOpportunity(opportunityId, {
            ...edit,
            estimated_value: edit.estimated_value === "" ? null : edit.estimated_value,
            probability: Number(edit.probability || 0),
            expected_close_date: edit.expected_close_date || null,
            updated_at: opportunity.updated_at,
        });
        setEditingSales(false);
    });

    const saveDesign = () => run(() => updateSolutionDesign(opportunityId, { ...designEdit, updated_at: opportunity.updated_at }));

    const submitPocRequest = () => run(async () => {
        await requestPoc({ opportunity_id: opportunityId, ...pocForm });
        setPocForm({ poc_name: "", objective: "", success_metric: "", exit_criteria: "", target_date: "", failure_condition: "", remarks: "" });
    });

    const stage = (target_stage) => run(() => transitionTechnicalStage(opportunityId, { target_stage, updated_at: opportunity.updated_at }));

    const close = (won) => {
        const reason = window.prompt(won ? "Optional close remarks" : "Closed Lost reason");
        if (!won && !reason?.trim()) return;
        return run(() => (won ? closeWon : closeLost)(opportunityId, { reason: reason || "", updated_at: opportunity.updated_at }));
    };

    if (!opportunity) {
        return <div className="standard-page"><div className="opp-loading">{error || "Loading opportunity…"}</div>{error && <Button onClick={load}><RefreshCw size={14} /> Retry</Button>}</div>;
    }

    const team = opportunity.team_members || [];
    const seMembers = team.filter(m => m.role === ROLES.SOLUTION_ENGINEER);
    const stageName = technicalStage || "—";
    const status = opportunity.status || "—";
    const probability = Number(opportunity.probability || 0);
    const isClosed = ["Closed Won", "Closed Lost"].includes(stageName) || status === "Closed";

    return (
        <div className="standard-page opp-detail-page fade-in">
            <PageHeader
                title="Opportunity Detail"
                description="Commercial context, technical execution and deal progress."
                actions={<>
                    <Button variant="secondary" onClick={() => navigate(-1)}><ArrowLeft size={14} /> Back</Button>
                    <Button variant="secondary" onClick={load}><RefreshCw size={14} /> Refresh</Button>
                </>}
            />

            {error && <div className="standard-error">{error}</div>}

            <Card className="opp-hero" padding={false}>
                <div className="opp-hero-main">
                    <div className="opp-eyebrow">Opportunity #{opportunityId}</div>
                    <div className="opp-title-row">
                        <div><h1>{opportunity.opportunity_name}</h1><p>{opportunity.account_name || `Account #${opportunity.account_id}`}</p></div>
                        <div className="opp-badges"><span className={statusClass(status)}>{status}</span><span className={statusClass(stageName)}>{stageName}</span></div>
                    </div>
                    <div className="opp-hero-stats">
                        <div><span>Estimated value</span><strong>{money(opportunity.estimated_value)}</strong></div>
                        <div><span>Probability</span><strong>{probability}%</strong></div>
                        <div><span>Expected close</span><strong>{dateLabel(opportunity.expected_close_date)}</strong></div>
                        <div><span>Lifecycle</span><strong>{opportunity.lifecycle_state || stageName}</strong></div>
                    </div>
                </div>
                <div className="opp-hero-side">
                    <div className="opp-progress-ring"><span>{probability}%</span><small>probability</small></div>
                    <div><span>Sales owner</span><strong>{opportunity.sales_owner?.full_name || "Pending assignment"}</strong></div>
                    <div><span>Created by</span><strong>{opportunity.created_by_user?.full_name || "Not recorded"}</strong></div>
                </div>
            </Card>

            <div className="opp-detail-grid">
                <Card>
                    <SectionHeader icon={FileText} title="Deal Overview" description="Core commercial information for this opportunity." action={canEditSales && <Button variant="ghost" size="sm" onClick={() => setEditingSales(v => !v)}><Edit3 size={13} /> {editingSales ? "Cancel" : "Edit"}</Button>} />
                    {editingSales ? (
                        <div className="opp-form-grid">
                            <label className="field-label"><span>Opportunity name</span><input value={edit.opportunity_name} onChange={e => setEdit({ ...edit, opportunity_name: e.target.value })} /></label>
                            <label className="field-label"><span>Expected close</span><input type="date" value={edit.expected_close_date} onChange={e => setEdit({ ...edit, expected_close_date: e.target.value })} /></label>
                            <label className="field-label"><span>Estimated value</span><input type="number" value={edit.estimated_value} onChange={e => setEdit({ ...edit, estimated_value: e.target.value })} /></label>
                            <label className="field-label"><span>Probability</span><input type="number" min="0" max="100" value={edit.probability} onChange={e => setEdit({ ...edit, probability: e.target.value })} /></label>
                            <label className="field-label opp-full"><span>Description</span><textarea rows="4" value={edit.description} onChange={e => setEdit({ ...edit, description: e.target.value })} /></label>
                            <div className="opp-form-actions opp-full"><Button disabled={saving} onClick={saveSales}><Save size={14} /> Save changes</Button></div>
                        </div>
                    ) : (
                        <>
                            <div className="opp-info-grid">
                                <InfoItem icon={DollarSign} label="Estimated value" value={money(opportunity.estimated_value)} />
                                <InfoItem icon={Target} label="Probability" value={`${probability}%`} />
                                <InfoItem icon={CalendarDays} label="Expected close" value={dateLabel(opportunity.expected_close_date)} />
                                <InfoItem icon={Users} label="Sales owner" value={opportunity.sales_owner?.full_name || "Pending assignment"} />
                            </div>
                            <div className="opp-description"><span>Description</span><p>{opportunity.description || "No description has been added yet."}</p></div>
                        </>
                    )}
                </Card>

                <Card>
                    <SectionHeader icon={Users} title="Ownership & Team" description="People currently contributing to this opportunity." />
                    <div className="opp-owner-list">
                        <div className="opp-person"><span className="opp-avatar">{(opportunity.sales_owner?.full_name || "S").charAt(0)}</span><div><small>Sales owner</small><strong>{opportunity.sales_owner?.full_name || "Pending assignment"}</strong></div></div>
                        {seMembers.map(member => <div className="opp-person" key={member.team_id}><span className="opp-avatar technical">{(member.user?.full_name || "S").charAt(0)}</span><div><small>Solution Engineer</small><strong>{member.user?.full_name || `User #${member.user_id}`}</strong></div></div>)}
                        {!seMembers.length && <Empty>No Solution Engineer is assigned yet.</Empty>}
                    </div>
                </Card>
            </div>

            {activeRole === ROLES.SALES_EXECUTIVE && opportunity.created_by === currentUserId && opportunity.status === "Open" && (
                <Card>
                    <SectionHeader icon={Zap} title="Sales Actions" description="Move the opportunity into the next commercial stage." />
                    <div className="opp-action-row">
                        {stageName === "Lead / Identified" && <Button disabled={saving} onClick={() => run(() => qualifyOpportunity(opportunityId))}><ArrowRight size={14} /> Qualify opportunity</Button>}
                        {stageName === "Qualification" && <Button disabled={saving} onClick={() => run(() => submitOpportunityForReview(opportunityId))}><ShieldCheck size={14} /> Submit for Sales Manager Review</Button>}
                        {!['Lead / Identified', 'Qualification'].includes(stageName) && <span className="opp-action-note">No sales action is required at the current stage.</span>}
                    </div>
                </Card>
            )}

            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && opportunity.is_active && (
                <Card>
                    <SectionHeader icon={Zap} title="Technical Progress" description="Control the technical lifecycle without manager approval gates." />
                    <div className="opp-stage-rail">
                        {['Qualification', 'Discovery', 'POC / Technical Evaluation', 'Proposal', 'Negotiation'].map((stageLabel, index) => <div className={stageName === stageLabel ? "active" : index < ['Qualification', 'Discovery', 'POC / Technical Evaluation', 'Proposal', 'Negotiation'].indexOf(stageName) ? "done" : ""} key={stageLabel}><span>{index + 1}</span><small>{stageLabel}</small></div>)}
                    </div>
                    <div className="opp-action-row">
                        {stageName === "Qualification" && <Button disabled={saving} onClick={() => stage("Discovery")}><ArrowRight size={14} /> Start Discovery</Button>}
                        {stageName === "Discovery" && <><Button disabled={saving} onClick={() => stage("POC / Technical Evaluation")}><ArrowRight size={14} /> Move to POC Evaluation</Button><Button variant="secondary" disabled={saving} onClick={() => stage("Proposal")}>Continue to Proposal</Button></>}
                        {stageName === "POC / Technical Evaluation" && <Button disabled={saving} onClick={() => stage("Proposal")}><ArrowRight size={14} /> Move to Proposal</Button>}
                        {stageName === "Proposal" && <Button disabled={saving} onClick={() => stage("Negotiation")}><ArrowRight size={14} /> Move to Negotiation</Button>}
                        {stageName === "Negotiation" && <><Button disabled={saving} onClick={() => close(true)}><CheckCircle2 size={14} /> Close Won</Button><Button variant="danger" disabled={saving} onClick={() => close(false)}><XCircle size={14} /> Close Lost</Button></>}
                        {isClosed && <span className="opp-action-note">This opportunity is closed.</span>}
                    </div>
                </Card>
            )}

            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && opportunity.is_active && (
                <div className="opp-detail-grid">
                    <Card>
                        <SectionHeader icon={FileText} title="Solution Design" description="Technical solution owned by the Solution Engineer." />
                        {canEditDesign ? <div className="opp-form-grid">
                            {[['solution_summary', 'Solution summary'], ['technical_approach', 'Technical approach'], ['technical_requirements', 'Technical requirements'], ['architecture_notes', 'Architecture / notes'], ['risks', 'Risks'], ['assumptions', 'Assumptions']].map(([key, label]) => <label className="field-label" key={key}><span>{label}</span><textarea rows="3" value={designEdit?.[key] || ""} onChange={e => setDesignEdit({ ...designEdit, [key]: e.target.value })} /></label>)}
                            <div className="opp-form-actions opp-full"><Button disabled={saving} onClick={saveDesign}><Save size={14} /> Save technical design</Button></div>
                        </div> : design ? <div className="opp-detail-text-grid">{[['Solution summary', design.solution_summary], ['Technical approach', design.technical_approach], ['Technical requirements', design.technical_requirements], ['Architecture / notes', design.architecture_notes], ['Risks', design.risks], ['Assumptions', design.assumptions]].map(([label, value]) => <div key={label}><span>{label}</span><p>{value || "—"}</p></div>)}</div> : <Empty>No solution design has been recorded.</Empty>}
                    </Card>

                    <Card>
                        <SectionHeader icon={Target} title="Request a POC" description="POCs are created directly as Approved; manager approval is no longer required." />
                        <div className="opp-form-stack">
                            {[['poc_name', 'POC name'], ['objective', 'Objective'], ['success_metric', 'Success criteria'], ['exit_criteria', 'Exit criteria'], ['failure_condition', 'Failure condition'], ['remarks', 'Technical remarks']].map(([key, label]) => <label className="field-label" key={key}><span>{label}</span><textarea rows={key === 'poc_name' ? 1 : 2} value={pocForm[key]} onChange={e => setPocForm({ ...pocForm, [key]: e.target.value })} /></label>)}
                            <label className="field-label"><span>Target date</span><input type="date" value={pocForm.target_date} onChange={e => setPocForm({ ...pocForm, target_date: e.target.value })} /></label>
                            <Button disabled={saving || !['Discovery', 'POC / Technical Evaluation'].includes(stageName)} onClick={submitPocRequest}><Zap size={14} /> Create POC</Button>
                        </div>
                    </Card>
                </div>
            )}

            <Card>
                <SectionHeader icon={Target} title="POC Execution" description="Track every technical proof of concept from request through completion." />
                {!pocs.length ? <Empty>No POCs have been created for this opportunity.</Empty> : <div className="opp-poc-list">
                    {pocs.map(poc => {
                        const form = resultForms[poc.poc_id] || { poc_access_link: poc.poc_access_link || "", outcome: poc.outcome || "Success", outcome_notes: poc.outcome_notes || "", remarks: poc.remarks || "" };
                        return <div className="opp-poc-card" key={poc.poc_id}>
                            <div className="opp-poc-head"><div><h3>{poc.poc_name}</h3><p>{poc.objective || "No objective provided."}</p></div><span className={statusClass(poc.status)}>{poc.status}</span></div>
                            <div className="opp-poc-meta"><span><Target size={12} /> {poc.success_metric || "No success criteria"}</span><span><CalendarDays size={12} /> {dateLabel(poc.target_date)}</span><span><Clock3 size={12} /> {poc.outcome || "Not completed"}</span></div>
                            <div className="opp-poc-grid"><div><span>Exit criteria</span><p>{poc.exit_criteria || "—"}</p></div><div><span>Failure condition</span><p>{poc.failure_condition || "—"}</p></div>{poc.outcome_notes && <div><span>Outcome notes</span><p>{poc.outcome_notes}</p></div>}</div>
                            {poc.poc_access_link && <a className="opp-poc-link" href={poc.poc_access_link} target="_blank" rel="noreferrer"><Link2 size={13} /> Open POC access</a>}
                            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && poc.status === "Approved" && <Button size="sm" disabled={saving} onClick={() => run(() => startPocExecution(poc.poc_id, { updated_at: poc.updated_at }))}><Zap size={13} /> Start POC</Button>}
                            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && poc.status === "In Progress" && <div className="opp-poc-result"><input placeholder="POC access link" value={form.poc_access_link} onChange={e => setResultForms({ ...resultForms, [poc.poc_id]: { ...form, poc_access_link: e.target.value } })} /><select value={form.outcome} onChange={e => setResultForms({ ...resultForms, [poc.poc_id]: { ...form, outcome: e.target.value } })}>{['Success', 'Failure', 'Ongoing', 'Abandoned'].map(x => <option key={x}>{x}</option>)}</select><textarea placeholder="Outcome notes" value={form.outcome_notes} onChange={e => setResultForms({ ...resultForms, [poc.poc_id]: { ...form, outcome_notes: e.target.value } })} /><textarea placeholder="Execution remarks" value={form.remarks} onChange={e => setResultForms({ ...resultForms, [poc.poc_id]: { ...form, remarks: e.target.value } })} /><Button disabled={saving} onClick={() => run(() => submitPocResult(poc.poc_id, { ...form, execution_status: "Submitted", updated_at: poc.updated_at }))}><MessageSquare size={13} /> Submit result</Button></div>}
                            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && poc.status === "Submitted" && <Button size="sm" disabled={saving} onClick={() => run(() => completePoc(poc.poc_id, { updated_at: poc.updated_at }))}><CheckCircle2 size={13} /> Complete after review</Button>}
                        </div>;
                    })}
                </div>}
            </Card>

            {activeRole === ROLES.SOLUTION_ENGINEER && assignedSE && opportunity.is_active && <Card>
                <SectionHeader icon={Users} title="Stakeholders" description="Customer contacts connected to this opportunity." />
                <StakeholderForm opportunityId={opportunityId} />
                <div className="opp-stakeholder-list">{stakeholders.map(s => <div className="opp-stakeholder" key={s.stakeholder_id}><span>{(s.stakeholder_name || "?").charAt(0)}</span><div><strong>{s.stakeholder_name}</strong><small>{s.designation || "Role not provided"}</small></div><small>{s.email || s.phone || "No contact details"}</small></div>)}{!stakeholders.length && <Empty>No stakeholders recorded.</Empty>}</div>
            </Card>}

            <Card>
                <SectionHeader icon={History} title="Stage History" description="Chronological record of opportunity movement." />
                {!history.length ? <Empty>No stage history recorded.</Empty> : <div className="opp-history">{history.map((entry, index) => <div className="opp-history-row" key={entry.history_id || index}><span className="opp-history-dot" /><div><strong>{entry.stage?.stage_name || `Stage #${entry.stage_id}`}</strong><small>{entry.user?.full_name || "System"}{entry.remarks ? ` · ${entry.remarks}` : ""}</small></div></div>)}</div>}
            </Card>
        </div>
    );
}
