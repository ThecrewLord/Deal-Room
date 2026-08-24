import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Edit3, Filter, Mail, RefreshCw, Search, ShieldCheck, UserCog, Users, UserX, X } from "lucide-react";
import adminApi from "../../api/adminApi";
import { AVAILABLE_ROLES, ROLES } from "../../auth/roles";
import { useAuth } from "../../context/AuthContext";
import "../../styles/admin.css";
import PageHeader from "../../components/ui/PageHeader";
import Button from "../../components/ui/Button";
import StatusBadge from "../../components/ui/StatusBadge";

export default function UserManagement() {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [editingRoles, setEditingRoles] = useState(null);
    const [editingManager, setEditingManager] = useState(null);
    const [saving, setSaving] = useState(false);
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("ALL");

    const load = async ({ refresh = false } = {}) => {
        try {
            refresh ? setRefreshing(true) : setLoading(true);
            setError("");
            setUsers(await adminApi.getUsers());
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load users.");
        } finally { setLoading(false); setRefreshing(false); }
    };
    useEffect(() => { load(); }, []);

    const revoke = async (user) => {
        if (user.user_id === currentUser?.user_id) return;
        if (!window.confirm(`Revoke access for ${user.full_name}?`)) return;
        try {
            setSaving(true); setError(""); setSuccess("");
            await adminApi.revoke(user.user_id);
            setSuccess(`Access revoked for ${user.full_name}.`);
            await load();
        } catch (err) { setError(err?.response?.data?.message || "Unable to revoke access."); }
        finally { setSaving(false); }
    };

    const visibleUsers = useMemo(() => {
        const query = search.trim().toLowerCase();
        return users.filter((user) => {
            const matchesStatus = status === "ALL" || user.status === status;
            const matchesSearch = !query || user.full_name?.toLowerCase().includes(query) || user.email?.toLowerCase().includes(query) || (user.roles || []).some((role) => role.toLowerCase().includes(query));
            return matchesStatus && matchesSearch;
        });
    }, [users, search, status]);

    const stats = useMemo(() => ({
        total: users.length,
        active: users.filter((u) => u.status === "APPROVED" && u.active).length,
        pending: users.filter((u) => u.status === "PENDING").length,
        revoked: users.filter((u) => u.status === "REVOKED").length,
    }), [users]);

    return (
        <div className="standard-page admin-page">
            <PageHeader title="User Management" description="Manage user accounts, roles and reporting relationships from a single workspace."
                actions={<Button variant="secondary" onClick={() => load({ refresh: true })} disabled={refreshing}><RefreshCw size={14} className={refreshing ? "admin-spin" : ""} /> Refresh</Button>} />

            <div className="admin-stat-grid compact">
                <MiniStat icon={Users} label="Total users" value={stats.total} />
                <MiniStat icon={ShieldCheck} label="Active" value={stats.active} tone="success" />
                <MiniStat icon={UserCog} label="Pending" value={stats.pending} tone="warning" />
                <MiniStat icon={UserX} label="Revoked" value={stats.revoked} tone="danger" />
            </div>

            {error && <div className="admin-alert admin-alert-error"><span>{error}</span></div>}
            {success && <div className="admin-alert admin-alert-success"><ShieldCheck size={16} /><span>{success}</span></div>}

            <div className="admin-toolbar-panel">
                <div className="admin-search"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name, email or role…" />{search && <button type="button" onClick={() => setSearch("")}><X size={14} /></button>}</div>
                <div className="admin-filter"><Filter size={15} /><select value={status} onChange={(e) => setStatus(e.target.value)}><option value="ALL">All statuses</option><option value="APPROVED">Approved</option><option value="PENDING">Pending</option><option value="REVOKED">Revoked</option></select><ChevronDown size={14} /></div>
                <span className="admin-result-count">{visibleUsers.length} of {users.length} users</span>
            </div>

            {loading ? <div className="admin-card"><AdminLoading label="Loading users…" /></div> : (
                <div className="admin-table-card"><div className="admin-table-wrap">
                    <table className="admin-table enhanced">
                        <thead><tr><th>User</th><th>Status</th><th>Roles</th><th>Manager</th><th>Organization</th><th>Actions</th></tr></thead>
                        <tbody>
                            {visibleUsers.length === 0 ? <tr><td colSpan="6"><div className="admin-table-empty"><Search size={20} /><strong>No users found</strong><span>Try changing your search or status filter.</span></div></td></tr> :
                                visibleUsers.map((user) => <tr key={user.user_id}>
                                    <td><div className="admin-table-user"><div className="admin-avatar">{getInitials(user.full_name)}</div><div><strong>{user.full_name}</strong><span><Mail size={11} />{user.email}</span></div></div></td>
                                    <td><StatusBadge status={user.status} /></td>
                                    <td><div className="role-chips">{(user.roles || []).map((role) => <span className="role-chip" key={role}>{shortRole(role)}</span>)}</div></td>
                                    <td>{user.manager_name || <span className="muted">No manager</span>}</td>
                                    <td>{formatOrganization(user.organization)}</td>
                                    <td><div className="admin-actions">
                                        <Button size="sm" variant="secondary" onClick={() => setEditingRoles(user)}><Edit3 size={12} /> Roles</Button>
                                        <Button size="sm" variant="secondary" onClick={() => setEditingManager(user)} disabled={user.status !== "APPROVED" || !user.active}>Manager</Button>
                                        {user.status === "APPROVED" && user.user_id !== currentUser?.user_id && <Button size="sm" variant="danger" onClick={() => revoke(user)} disabled={saving}><UserX size={12} /> Revoke</Button>}
                                    </div></td>
                                </tr>)}
                        </tbody>
                    </table>
                </div></div>
            )}

            {editingRoles && <RoleEditorModal user={editingRoles} onClose={() => setEditingRoles(null)} onSaved={(message) => { setEditingRoles(null); setSuccess(message); load(); }} onError={setError} />}
            {editingManager && <ManagerEditorModal user={editingManager} onClose={() => setEditingManager(null)} onSaved={(message) => { setEditingManager(null); setSuccess(message); load(); }} onError={setError} />}
        </div>
    );
}

function RoleEditorModal({ user, onClose, onSaved, onError }) {
    const [roles, setRoles] = useState(user.roles || []);
    const [managerId, setManagerId] = useState(user.manager_id ?? null);
    const [candidates, setCandidates] = useState([]);
    const [candidateLoading, setCandidateLoading] = useState(false);
    const [candidateError, setCandidateError] = useState("");
    const [saving, setSaving] = useState(false);
    const managerRequired = roles.some((role) => [ROLES.SALES_EXECUTIVE, ROLES.SOLUTION_ENGINEER, ROLES.SOLUTION_ENGINEER].includes(role));

    useEffect(() => {
        let mounted = true;
        setCandidateLoading(true); setCandidateError("");
        adminApi.getManagerCandidates(user.user_id, roles).then((items) => mounted && setCandidates(items || []))
            .catch((err) => mounted && setCandidateError(err?.response?.data?.message || "Unable to load eligible managers."))
            .finally(() => mounted && setCandidateLoading(false));
        return () => { mounted = false; };
    }, [user.user_id, roles]);

    useEffect(() => {
        if (!managerRequired) setManagerId(null);
        else if (!candidates.some((candidate) => candidate.user_id === managerId)) setManagerId(null);
    }, [managerRequired, candidates, managerId]);

    const toggle = (role) => setRoles((current) => current.includes(role) ? current.filter((item) => item !== role) : [...current, role]);
    const save = async () => {
        if (!roles.length) return onError("At least one role is required.");
        if (managerRequired && !managerId) return onError("Select a valid manager for the selected roles.");
        if (!managerRequired && managerId !== null) return onError("The selected roles require No Manager.");
        if (roles.includes(ROLES.ADMIN) && !user.roles.includes(ROLES.ADMIN) && !window.confirm("This gives the user full access-administration privileges. Continue?")) return;
        try {
            setSaving(true); onError("");
            await adminApi.updateRoles(user.user_id, roles, user.updated_at, managerId);
            onSaved(`Roles updated for ${user.full_name}.`);
        } catch (err) { onError(err?.response?.data?.message || "Unable to update roles."); }
        finally { setSaving(false); }
    };

    return <Modal title="Manage roles" subtitle={user.full_name} onClose={onClose}>
        <div className="admin-modal-user"><div className="admin-avatar large">{getInitials(user.full_name)}</div><div><strong>{user.full_name}</strong><span>{user.email}</span></div></div>
        <div className="admin-modal-section"><div className="admin-section-label"><span>Roles</span><small>{roles.length} selected</small></div><div className="admin-role-grid">{AVAILABLE_ROLES.map((role) => <label className={`admin-role-option ${roles.includes(role) ? "selected" : ""}`} key={role}><input type="checkbox" checked={roles.includes(role)} onChange={() => toggle(role)} /><span className="admin-role-check"><ShieldCheck size={14} /></span>{role}</label>)}</div></div>
        <div className="admin-modal-section"><div className="admin-section-label"><span>Reporting manager</span><small>{managerRequired ? "Required" : "Not required"}</small></div><label className={`admin-select ${!managerRequired ? "disabled" : ""}`}><Users size={15} /><select value={managerId ?? ""} onChange={(e) => setManagerId(e.target.value ? Number(e.target.value) : null)} disabled={candidateLoading || !managerRequired}>{!managerRequired && <option value="">No Manager</option>}{managerRequired && <option value="">Select manager</option>}{candidates.map((candidate) => <option key={candidate.user_id} value={candidate.user_id}>{candidate.full_name} — {candidate.email}</option>)}</select><ChevronDown size={14} /></label>{candidateLoading && <div className="admin-inline-note">Finding eligible managers…</div>}{candidateError && <div className="admin-inline-error">{candidateError}</div>}</div>
        <div className="admin-modal-actions"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button onClick={save} disabled={saving || candidateLoading}>{saving ? "Saving…" : "Save changes"}</Button></div>
    </Modal>;
}

function ManagerEditorModal({ user, onClose, onSaved, onError }) {
    const [candidates, setCandidates] = useState([]);
    const [managerId, setManagerId] = useState(user.manager_id ?? null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    useEffect(() => {
        adminApi.getManagerCandidates(user.user_id, user.roles || []).then((items) => setCandidates(items || []))
            .catch((err) => onError(err?.response?.data?.message || "Unable to load eligible managers.")).finally(() => setLoading(false));
    }, [user.user_id, user.roles]);
    const save = async () => {
        try { setSaving(true); onError(""); await adminApi.updateManager(user.user_id, managerId, user.updated_at); onSaved(`Manager updated for ${user.full_name}.`); }
        catch (err) { onError(err?.response?.data?.message || "Unable to update manager."); }
        finally { setSaving(false); }
    };
    return <Modal title="Change manager" subtitle={user.full_name} onClose={onClose}>
        <div className="admin-modal-user"><div className="admin-avatar large">{getInitials(user.full_name)}</div><div><strong>{user.full_name}</strong><span>{user.email}</span></div></div>
        <div className="admin-current-value"><small>Current manager</small><strong>{user.manager_name || "No manager assigned"}</strong></div>
        <label className="admin-select"><Users size={15} /><select value={managerId ?? ""} onChange={(e) => setManagerId(e.target.value ? Number(e.target.value) : null)} disabled={loading}><option value="">No Manager</option>{candidates.map((candidate) => <option key={candidate.user_id} value={candidate.user_id}>{candidate.full_name} — {candidate.email}</option>)}</select><ChevronDown size={14} /></label>
        {loading && <div className="admin-inline-note">Loading eligible managers…</div>}
        <div className="admin-modal-actions"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button onClick={save} disabled={saving || loading}>{saving ? "Saving…" : "Save manager"}</Button></div>
    </Modal>;
}

function Modal({ title, subtitle, children, onClose }) {
    return <div className="admin-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}><div className="admin-modal" role="dialog" aria-modal="true"><div className="admin-modal-header"><div><h3>{title}</h3><p>{subtitle}</p></div><button type="button" onClick={onClose} aria-label="Close"><X size={17} /></button></div><div className="admin-modal-body">{children}</div></div></div>;
}
function MiniStat({ icon: Icon, label, value, tone = "" }) { return <div className="admin-mini-stat"><span className={`admin-mini-icon ${tone}`}><Icon size={16} /></span><span><small>{label}</small><strong>{value}</strong></span></div>; }
function AdminLoading({ label }) { return <div className="admin-loading"><span className="admin-spinner" />{label}</div>; }
function getInitials(name) { return String(name || "U").trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase(); }
function shortRole(role) { return role.replace(" Manager", " Mgr").replace("Solution Engineer", "Solutions"); }
function formatOrganization(value) { return value ? value.replaceAll("_", " ").replace("PRE SALES TECHNICAL", "Pre-Sales / Technical").replace("ADMINISTRATION", "Administration").replace("SALES", "Sales") : "—"; }
