import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, RefreshCw, Search, Users } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import { useAuth } from "../context/AuthContext";
import { ROLES } from "../auth/roles";
import { getPocAssignmentQueue, getPocTeamCandidates, assignPocTeam, reassignPocTeam } from "../api/deliveryManagerApi";
import "../styles/delivery-manager.css";

export default function DeliveryManagerPocAssignment() {
    const { activeRole } = useAuth();
    const navigate = useNavigate();
    const [rows, setRows] = useState([]); const [candidates, setCandidates] = useState([]);
    const [selectedId, setSelectedId] = useState(null); const [selectedMembers, setSelectedMembers] = useState([]);
    const [search, setSearch] = useState(""); const [status, setStatus] = useState("all");
    const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
    const load = useCallback(async () => {
        try { setLoading(true); setError(""); const [queue, team] = await Promise.all([getPocAssignmentQueue({ search, status }), getPocTeamCandidates()]); setRows(queue); setCandidates(team); }
        catch (e) { setError(e?.response?.data?.message || "Unable to load POC team assignments."); }
        finally { setLoading(false); }
    }, [search, status]);
    useEffect(() => { if (activeRole === ROLES.DELIVERY_MANAGER || activeRole === ROLES.LEADERSHIP) { const timer = setTimeout(() => load(), 250); return () => clearTimeout(timer); } }, [activeRole, load]);
    const selected = useMemo(() => rows.find(row => row.opportunity_id === selectedId) || null, [rows, selectedId]);
    const displayedCandidates = useMemo(() => { const byId = new Map(candidates.map(member => [member.user_id, member])); (selected?.team || []).forEach(member => { if (!byId.has(member.user_id)) byId.set(member.user_id, member); }); return [...byId.values()].sort((a, b) => (a.full_name || "").localeCompare(b.full_name || "")); }, [candidates, selected]);
    useEffect(() => { if (selected) setSelectedMembers((selected.team || []).map(member => member.user_id)); else setSelectedMembers([]); }, [selectedId, selected?.poc?.row_version, selected?.row_version]);
    const toggle = id => setSelectedMembers(prev => prev.includes(id) ? prev.filter(value => value !== id) : [...prev, id]);
    const save = async () => {
        if (!selected) return;
        if (!selectedMembers.length || selectedMembers.length > 2) { setError("Select one or two eligible team members."); return; }
        try {
            setSaving(true); setError(""); setNotice("");
            if (selected.team_assigned) await reassignPocTeam(selected.opportunity_id, selectedMembers, selected.row_version);
            else await assignPocTeam(selected.poc.poc_id, selectedMembers, selected.poc.row_version);
            setNotice("POC team assignment saved."); await load();
        } catch (e) { setError(e?.response?.data?.message || "Unable to save the POC team. Refresh and retry."); }
        finally { setSaving(false); }
    };
    if (activeRole !== ROLES.DELIVERY_MANAGER && activeRole !== ROLES.LEADERSHIP) return <div className="standard-page"><PageHeader title="POC Team Assignment" description="You do not have access to this page." /></div>;
    return <div className="standard-page delivery-manager-page">
        <PageHeader title="POC Team Assignment" description="Assign the initial POC team once per opportunity. Repeat POC cycles inherit the canonical team." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button>} />
        {error && <ErrorState message={error} onRetry={load} />}{notice && <div className="dm-success" role="status"><Check size={15}/>{notice}</div>}
        <div className="dm-assignment-grid">
            <Card padding={false}>
                <div className="dm-card-toolbar"><div><h2>POC opportunities</h2><p>Open opportunities in the POC stage with an active POC cycle.</p></div>
                    <div className="dm-filters"><label className="ui-search"><Search size={14}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search opportunities" /></label><select value={status} onChange={e => setStatus(e.target.value)}><option value="all">All assignments</option><option value="unassigned">Needs assignment</option><option value="assigned">Assigned</option></select></div>
                </div>
                {loading ? <LoadingState message="Loading POC opportunities…"/> : <div className="dm-list">{rows.map(row => <button type="button" key={row.opportunity_id} className={`dm-list-row ${selectedId === row.opportunity_id ? "selected" : ""}`} onClick={() => { setSelectedId(row.opportunity_id); setNotice(""); setError(""); }}><span className="dm-list-main"><strong>{row.opportunity_name}</strong><small>{row.account_name || "Account unavailable"} · {row.poc?.poc_name}</small></span><span className={`dm-status ${row.team_assigned ? "assigned" : "pending"}`}>{row.team_assigned ? "Assigned" : "Needs assignment"}</span></button>)}{!rows.length && <EmptyState message="No active POC opportunities match these filters."/>}</div>}
            </Card>
            <Card>
                <div className="dm-card-title"><span className="dm-icon"><Users size={17}/></span><div><h2>{selected?.opportunity_name || "Select an opportunity"}</h2><p>{selected ? `${selected.account_name || "Account unavailable"} · ${selected.poc?.status || "Active POC"}` : "Choose an opportunity to review its POC team."}</p></div></div>
                {selected && <>
                    <div className="dm-context-grid"><div><small>Lifecycle stage</small><strong>{selected.stage}</strong></div><div><small>POC target date</small><strong>{selected.poc?.target_date || "—"}</strong></div></div>
                    <div className="dm-member-section"><h3>{selected.team_assigned ? "Current POC team" : "Assign POC team"}</h3><p>Choose one or two active, approved DevOps Engineers or Data Analysts. Changes are explicit and audited.{selected.active_poc ? "" : " The latest POC cycle is complete; reassignment updates the opportunity-level team for the next cycle."}</p>
                        {displayedCandidates.map(member => <label className="dm-member-option" key={member.user_id}><input type="checkbox" checked={selectedMembers.includes(member.user_id)} onChange={() => toggle(member.user_id)} disabled={!selectedMembers.includes(member.user_id) && selectedMembers.length >= 2}/><span><strong>{member.full_name}{member.active === false ? " (inactive — remove or replace)" : ""}</strong><small>{(member.roles || [member.role]).filter(role => ["DevOps Engineer", "Data Analyst"].includes(role)).join(" · ")}</small></span></label>)}
                        {!displayedCandidates.length && <EmptyState message="No eligible POC team members are available."/>}
                    </div>
                    {(selected.team || []).some(member => !member.active) && <p className="dm-warning">An existing member is inactive or unapproved. Select eligible replacements before saving; the system will not silently substitute anyone.</p>}
                    {!selected.team_editable && <p className="dm-warning">Team changes are blocked while a POC result is submitted and awaiting completion.</p>}
                    <div className="dm-actions"><Button variant="secondary" onClick={() => navigate(`/opportunity/${selected.opportunity_id}`)}>Open opportunity</Button><Button onClick={save} disabled={saving || !selectedMembers.length || !selected.team_editable}>{saving ? "Saving…" : selected.team_assigned ? "Save reassignment" : "Assign team"}</Button></div>
                </>}
            </Card>
        </div>
    </div>;
}
