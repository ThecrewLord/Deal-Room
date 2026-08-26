import { useEffect, useMemo, useState } from "react";
import { BriefcaseBusiness, Check, CheckCircle2, ChevronDown, RefreshCw, Search, Users, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { finalizePreSalesAssignment, getEligibleSolutionEngineers, getPendingPreSalesAssignments } from "../api/preSalesAssignmentApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import StageBadge from "../components/ui/StageBadge";
import KpiCard from "../components/ui/KpiCard";

const money = (value) => {
    const n = Number(value || 0);
    if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `$${(n / 1000).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
};

function ResourcePicker({ label, users, selected, onChange, tone = "blue" }) {
    const [open, setOpen] = useState(false);
    const selectedUsers = users.filter(u => selected.includes(String(u.user_id)));
    const toggle = id => {
        const value = String(id);
        onChange(selected.includes(value) ? selected.filter(x => x !== value) : [...selected, value]);
    };
    return <div className={`psm-resource-picker ${tone}`}>
        <div className="psm-resource-label"><span>{label}</span><small>{selected.length} selected</small></div>
        <button type="button" className={`psm-resource-trigger ${open ? "open" : ""}`} onClick={() => setOpen(x => !x)}>
            <span>{selectedUsers.length ? selectedUsers.map(x => x.full_name).join(", ") : `Select ${label.toLowerCase()}`}</span><ChevronDown size={15}/>
        </button>
        {open && <div className="psm-resource-menu">
            {users.map(user => { const checked = selected.includes(String(user.user_id)); return <label key={user.user_id} className={`psm-resource-option ${checked ? "selected" : ""}`}><input type="checkbox" checked={checked} onChange={() => toggle(user.user_id)}/><span className="psm-resource-avatar">{user.full_name?.split(/\s+/).map(x => x[0]).slice(0,2).join("").toUpperCase()}</span><span><b>{user.full_name}</b><small>{user.email || "Approved technical user"}</small></span>{checked && <Check size={14}/>}</label>; })}
            {!users.length && <div className="psm-resource-empty">No eligible users available.</div>}
            <div className="psm-resource-menu-footer"><button type="button" onClick={() => setOpen(false)}>Done</button></div>
        </div>}
        {selectedUsers.length > 0 && <div className="psm-selected-chips">{selectedUsers.map(user => <span key={user.user_id}>{user.full_name}<button type="button" aria-label={`Remove ${user.full_name}`} onClick={() => toggle(user.user_id)}><X size={11}/></button></span>)}</div>}
    </div>;
}

export default function PreSalesAssignment() {
    const { activeRole } = useAuth(); const navigate = useNavigate();
    const [queue, setQueue] = useState([]); const [solutionEngineers, setSolutionEngineers] = useState([]);
    const [selection, setSelection] = useState({}); const [busy, setBusy] = useState(null); const [error, setError] = useState(""); const [search, setSearch] = useState("");
    const load = async () => { try { setError(""); const [pending, engineers] = await Promise.all([getPendingPreSalesAssignments(), getEligibleSolutionEngineers()]); setQueue(pending || []); setSolutionEngineers(engineers || []); } catch (err) { setError(err?.response?.data?.message || "Unable to load technical assignments."); } };
    useEffect(() => { if (activeRole === ROLES.PRE_SALES_MANAGER) load(); }, [activeRole]);
    const update = (id, field, values) => setSelection(p => ({ ...p, [id]: { ...(p[id] || {}), [field]: values } }));
    const finalize = async o => { const current = selection[o.opportunity_id] || {}; const solution_engineer_ids = (current.solution_engineer_ids || []).map(Number); if (!solution_engineer_ids.length) { setError("Select at least one Solution Engineer before finalizing."); return; } try { setBusy(o.opportunity_id); setError(""); await finalizePreSalesAssignment(o.opportunity_id, { solution_engineer_ids, delivery_ids: [], updated_at: o.updated_at }); await load(); setSelection(p => { const n = { ...p }; delete n[o.opportunity_id]; return n; }); } catch (err) { setError(err?.response?.data?.message || "Unable to finalize technical assignment."); } finally { setBusy(null); } };
    const filtered = useMemo(() => { const q = search.trim().toLowerCase(); return queue.filter(o => !q || `${o.opportunity_name} ${o.account_name || ""} ${o.sales_owner?.full_name || ""}`.toLowerCase().includes(q)); }, [queue, search]);
    const assignedCount = Object.values(selection).filter(x => (x.solution_engineer_ids || []).length && (x.delivery_ids || []).length).length;
    const totalValue = queue.reduce((sum, x) => sum + Number(x.estimated_value || 0), 0);
    if (activeRole !== ROLES.PRE_SALES_MANAGER) return <div className="standard-page"><PageHeader title="Technical Assignment" description="You do not have access to this page." /></div>;
    return <div className="standard-page psm-work-page fade-in">
        <PageHeader title="Technical Assignment" description="Assign Solution Engineers to approved opportunities and manage technical ownership." actions={<><Button variant="ghost" onClick={() => navigate("/pre-sales/team-performance")}><Users size={14}/> Team Performance</Button><Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button></>} />
        {error && <div className="standard-error">{error}</div>}
        <div className="psm-assignment-overview ui-kpi-grid">
            <KpiCard icon={BriefcaseBusiness} label="Awaiting assignment" value={queue.length} description={`${money(totalValue)} total opportunity value`} />
            <KpiCard icon={Users} label="Eligible Solution Engineers" value={solutionEngineers.length} description="Available for allocation" />
            <KpiCard icon={CheckCircle2} label="Ready to finalize" value={assignedCount} description="Complete technical teams selected" tone="success" className="psm-kpi-success" />
        </div>
        <Card padding={false} className="psm-assignment-shell">
            <div className="psm-assignment-toolbar"><div><div className="psm-eyebrow">WORK QUEUE</div><h2>Approved opportunities awaiting technical ownership</h2><p>Assign one or more technical resources, then finalize the handoff.</p></div><label className="ui-search"><Search size={14}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search opportunity, account or sales owner…" /></label></div>
            <div className="psm-assignment-list">
                {filtered.map(o => { const current = selection[o.opportunity_id] || {}; const selectedTotal = (current.solution_engineer_ids || []).length; const ready = selectedTotal > 0; return <article key={o.opportunity_id} className={`psm-assignment-card-v2 ${ready ? "ready" : ""}`}>
                    <div className="psm-assignment-topline"><div><button className="record-link-title" onClick={() => navigate(`/opportunity/${o.opportunity_id}`)}>{o.opportunity_name}</button><p>{o.account_name || `Account #${o.account_id}`} <span>•</span> Sales owner: {o.sales_owner?.full_name || "Unassigned"}</p></div><StageBadge stage={o.current_stage?.stage_name}/></div>
                    <div className="psm-deal-summary"><div><span>Deal value</span><strong>{money(o.estimated_value)}</strong></div><div><span>Probability</span><strong>{o.probability ?? 0}%</strong></div><div><span>Expected close</span><strong>{o.expected_close_date || "—"}</strong></div><div><span>Team selected</span><strong>{selectedTotal}</strong></div></div>
                    <div className="psm-resource-grid"><ResourcePicker label="Solution Engineer(s)" users={solutionEngineers} selected={current.solution_engineer_ids || []} onChange={v => update(o.opportunity_id, "solution_engineer_ids", v)} /></div>
                    <div className="psm-assignment-footer"><span className={ready ? "ready-text" : ""}>{ready ? <><CheckCircle2 size={14}/> Technical team complete</> : <><Users size={14}/> Select at least one Solution Engineer</>}</span><Button disabled={busy === o.opportunity_id || !ready} onClick={() => finalize(o)}><CheckCircle2 size={14}/>{busy === o.opportunity_id ? "Finalizing…" : "Finalize Assignment"}</Button></div>
                </article>; })}
                {!filtered.length && <EmptyState message={queue.length ? "No assignments match your search." : "No opportunities are awaiting technical assignment."}/>} 
            </div>
        </Card>
    </div>;
}
