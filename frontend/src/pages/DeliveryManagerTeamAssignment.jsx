import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, RefreshCw, Search, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/ui/PageHeader";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import { useAuth } from "../context/AuthContext";
import { ROLES } from "../auth/roles";
import { getDeliveryAssignmentQueue, getDeliveryTeamCandidates, assignDeliveryTeam } from "../api/deliveryManagerApi";
import "../styles/delivery-manager.css";

export default function DeliveryManagerTeamAssignment() {
    const { activeRole } = useAuth(); const navigate = useNavigate();
    const [rows, setRows] = useState([]); const [candidates, setCandidates] = useState([]); const [selectedId, setSelectedId] = useState(null); const [selectedMembers, setSelectedMembers] = useState([]);
    const [search, setSearch] = useState(""); const [status, setStatus] = useState("all"); const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState("");
    const load = useCallback(async () => { try { setLoading(true); setError(""); const [queue, team] = await Promise.all([getDeliveryAssignmentQueue({ search, status }), getDeliveryTeamCandidates()]); setRows(queue); setCandidates(team); } catch (e) { setError(e?.response?.data?.message || "Unable to load delivery assignments."); } finally { setLoading(false); } }, [search, status]);
    useEffect(() => { if (activeRole === ROLES.DELIVERY_MANAGER || activeRole === ROLES.LEADERSHIP) { const timer = setTimeout(() => load(), 250); return () => clearTimeout(timer); } }, [activeRole, load]);
    const selected = useMemo(() => rows.find(row => row.delivery_project_id === selectedId) || null, [rows, selectedId]);
    const displayedCandidates = useMemo(() => { const byId = new Map(candidates.map(member => [member.user_id, member])); [...(selected?.members || []), ...(selected?.suggested_members || [])].forEach(member => { if (!byId.has(member.user_id)) byId.set(member.user_id, member); }); return [...byId.values()].sort((a, b) => (a.full_name || "").localeCompare(b.full_name || "")); }, [candidates, selected]);
    useEffect(() => { if (selected) setSelectedMembers(selected.team_assigned ? selected.members.map(member => member.user_id) : selected.suggested_members.map(member => member.user_id)); else setSelectedMembers([]); }, [selectedId, selected?.row_version]);
    const toggle = id => setSelectedMembers(prev => prev.includes(id) ? prev.filter(value => value !== id) : [...prev, id]);
    const save = async () => { if (!selected) return; try { setSaving(true); setError(""); setNotice(""); await assignDeliveryTeam(selected.delivery_project_id, selectedMembers, selected.row_version); setNotice("Delivery team assignment saved."); await load(); } catch (e) { setError(e?.response?.data?.message || "Unable to save the delivery team. Refresh and retry."); } finally { setSaving(false); } };
    if (activeRole !== ROLES.DELIVERY_MANAGER && activeRole !== ROLES.LEADERSHIP) return <div className="standard-page"><PageHeader title="Delivery Team Assignment" description="You do not have access to this page." /></div>;
    return <div className="standard-page delivery-manager-page"><PageHeader title="Delivery Team Assignment" description="Review the suggested POC members, then confirm the separate delivery team." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14}/> Refresh</Button>}/>
        {error && <ErrorState message={error} onRetry={load} />}{notice && <div className="dm-success" role="status"><Check size={15}/>{notice}</div>}
        <div className="dm-assignment-grid"><Card padding={false}><div className="dm-card-toolbar"><div><h2>Delivery opportunities</h2><p>Projects created by the existing Closed Won workflow.</p></div><div className="dm-filters"><label className="ui-search"><Search size={14}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search opportunities"/></label><select value={status} onChange={e => setStatus(e.target.value)}><option value="all">All assignments</option><option value="unassigned">Needs assignment</option><option value="assigned">Assigned</option></select></div></div>
        {loading ? <LoadingState message="Loading delivery projects…"/> : <div className="dm-list">{rows.map(row => <button type="button" key={row.delivery_project_id} className={`dm-list-row ${selectedId === row.delivery_project_id ? "selected" : ""}`} onClick={() => { setSelectedId(row.delivery_project_id); setError(""); setNotice(""); }}><span className="dm-list-main"><strong>{row.opportunity_name}</strong><small>{row.account_name || "Account unavailable"} · {row.status}</small></span><span className={`dm-status ${row.team_assigned ? "assigned" : "pending"}`}>{row.team_assigned ? "Assigned" : "Needs assignment"}</span></button>)}{!rows.length && <EmptyState message="No delivery projects match these filters. Delivery projects are created by the existing Closed Won workflow."/>}</div>}</Card>
        <Card><div className="dm-card-title"><span className="dm-icon"><Users size={17}/></span><div><h2>{selected?.opportunity_name || "Select a delivery project"}</h2><p>{selected ? `${selected.account_name || "Account unavailable"} · ${selected.status}` : "Select a project to confirm team membership."}</p></div></div>
        {selected && <><div className="dm-context-grid"><div><small>Lifecycle stage</small><strong>{selected.stage || "—"}</strong></div><div><small>Suggested POC members</small><strong>{selected.suggested_members.length}</strong></div></div>
            {!selected.suggested_members.length && <p className="dm-warning">This opportunity has no existing POC team. Select eligible members explicitly; no members are fabricated.</p>}
            <div className="dm-member-section"><h3>{selected.team_assigned ? "Current delivery team" : "Confirm delivery team"}</h3><p>Delivery membership is independent from POC membership. Suggested members are preselected only as a starting point.</p>{displayedCandidates.map(member => <label className="dm-member-option" key={member.user_id}><input type="checkbox" checked={selectedMembers.includes(member.user_id)} onChange={() => toggle(member.user_id)}/><span><strong>{member.full_name}{member.active === false ? " (inactive — remove or replace)" : ""}</strong><small>{(member.roles || [member.role]).filter(role => ["DevOps Engineer", "Data Analyst"].includes(role)).join(" · ")}</small></span></label>)}</div>
            <div className="dm-actions"><Button variant="secondary" onClick={() => navigate(`/opportunity/${selected.opportunity_id}`)}>Open opportunity</Button><Button onClick={save} disabled={saving || !selectedMembers.length}>{saving ? "Saving…" : "Save delivery team"}</Button></div>
        </>}</Card></div>
    </div>;
}
