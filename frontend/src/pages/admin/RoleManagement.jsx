import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, Edit3, RefreshCw, Search, ShieldCheck, Users, X } from "lucide-react";
import adminApi from "../../api/adminApi";
import { AVAILABLE_ROLES, ROLES } from "../../auth/roles";
import "../../styles/admin.css";
import PageHeader from "../../components/ui/PageHeader";
import Button from "../../components/ui/Button";
import StatusBadge from "../../components/ui/StatusBadge";

const roleDescriptions = {
    [ROLES.ADMIN]: "Platform administration and access control",
    [ROLES.SALES_MANAGER]: "Sales team leadership and pipeline review",
    [ROLES.PRE_SALES_MANAGER]: "Pre-sales assignment and technical oversight",
    [ROLES.SALES_EXECUTIVE]: "Opportunity ownership and account execution",
    [ROLES.SOLUTION_ENGINEER]: "Technical discovery, POCs, solution design and execution",
};

export default function RoleManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [search, setSearch] = useState("");
    const [selectedRole, setSelectedRole] = useState("ALL");
    const [editing, setEditing] = useState(null);

    const load = async ({ refresh = false } = {}) => {
        try {
            refresh ? setRefreshing(true) : setLoading(true);
            setError("");
            setUsers(await adminApi.getUsers());
        } catch (err) { setError(err?.response?.data?.message || "Unable to load role assignments."); }
        finally { setLoading(false); setRefreshing(false); }
    };
    useEffect(() => { load(); }, []);

    const roleCounts = useMemo(() => AVAILABLE_ROLES.map((role) => ({
        role, count: users.filter((user) => (user.roles || []).includes(role)).length,
    })), [users]);

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        return users.filter((user) => {
            const matchesRole = selectedRole === "ALL" || (user.roles || []).includes(selectedRole);
            const matchesSearch = !q || user.full_name?.toLowerCase().includes(q) || user.email?.toLowerCase().includes(q);
            return matchesRole && matchesSearch;
        });
    }, [users, selectedRole, search]);

    return <div className="standard-page admin-page">
        <PageHeader title="Role Management" description="Review role assignments and update responsibilities without leaving the administration workspace."
            actions={<Button variant="secondary" onClick={() => load({ refresh: true })} disabled={refreshing}><RefreshCw size={14} className={refreshing ? "admin-spin" : ""} /> Refresh</Button>} />

        <div className="admin-role-overview">
            {roleCounts.map(({ role, count }) => <button key={role} type="button" className={`admin-role-summary ${selectedRole === role ? "selected" : ""}`} onClick={() => setSelectedRole(selectedRole === role ? "ALL" : role)}>
                <span className="admin-role-summary-icon"><ShieldCheck size={15} /></span><span><strong>{count}</strong><small>{role}</small></span>
            </button>)}
        </div>

        {error && <div className="admin-alert admin-alert-error"><span>{error}</span></div>}
        {success && <div className="admin-alert admin-alert-success"><CheckCircle2 size={16} /><span>{success}</span></div>}

        <div className="admin-toolbar-panel">
            <div className="admin-search"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or email…" />{search && <button type="button" onClick={() => setSearch("")}><X size={14} /></button>}</div>
            <div className="admin-filter"><Users size={15} /><select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)}><option value="ALL">All roles</option>{AVAILABLE_ROLES.map((role) => <option key={role} value={role}>{role}</option>)}</select><ChevronDown size={14} /></div>
            <span className="admin-result-count">{visible.length} users</span>
        </div>

        {loading ? <div className="admin-card"><AdminLoading label="Loading role assignments…" /></div> : <div className="admin-table-card"><div className="admin-table-wrap">
            <table className="admin-table enhanced">
                <thead><tr><th>User</th><th>Assigned roles</th><th>Manager</th><th>Organization</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>{visible.length === 0 ? <tr><td colSpan="6"><div className="admin-table-empty"><Search size={20} /><strong>No matching assignments</strong><span>Try another role or search term.</span></div></td></tr> : visible.map((user) => <tr key={user.user_id}>
                    <td><div className="admin-table-user"><div className="admin-avatar">{getInitials(user.full_name)}</div><div><strong>{user.full_name}</strong><span>{user.email}</span></div></div></td>
                    <td><div className="role-chips">{(user.roles || []).map((role) => <span className="role-chip" key={role}>{role}</span>)}</div></td>
                    <td>{user.manager_name || <span className="muted">No manager</span>}</td><td>{formatOrganization(user.organization)}</td><td><StatusBadge status={user.status} /></td>
                    <td><Button size="sm" variant="secondary" onClick={() => setEditing(user)}><Edit3 size={12} /> Edit roles</Button></td>
                </tr>)}</tbody>
            </table>
        </div></div>}

        {editing && <RoleEditor user={editing} onClose={() => setEditing(null)} onSaved={(message) => { setEditing(null); setSuccess(message); load(); }} onError={setError} />}
    </div>;
}

function RoleEditor({ user, onClose, onSaved, onError }) {
    const [roles, setRoles] = useState(user.roles || []);
    const [managerId, setManagerId] = useState(user.manager_id ?? null);
    const [candidates, setCandidates] = useState([]);
    const [loadingCandidates, setLoadingCandidates] = useState(true);
    const [saving, setSaving] = useState(false);
    const [candidateError, setCandidateError] = useState("");
    const managerRequired = roles.some((role) => [ROLES.SALES_EXECUTIVE, ROLES.SOLUTION_ENGINEER, ROLES.SOLUTION_ENGINEER].includes(role));

    useEffect(() => {
        let mounted = true;
        setLoadingCandidates(true); setCandidateError("");
        adminApi.getManagerCandidates(user.user_id, roles).then((items) => mounted && setCandidates(items || []))
            .catch((err) => mounted && setCandidateError(err?.response?.data?.message || "Unable to load eligible managers."))
            .finally(() => mounted && setLoadingCandidates(false));
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
        if (user.roles.some((r) => [ROLES.ADMIN, ROLES.SALES_MANAGER, ROLES.PRE_SALES_MANAGER].includes(r) && !roles.includes(r)) && !window.confirm("This removes a privileged role. Continue?")) return;
        try { setSaving(true); onError(""); await adminApi.updateRoles(user.user_id, roles, user.updated_at, managerId); onSaved(`Roles updated for ${user.full_name}.`); }
        catch (err) { onError(err?.response?.data?.message || "Unable to update roles."); }
        finally { setSaving(false); }
    };

    return <div className="admin-modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
        <div className="admin-modal" role="dialog" aria-modal="true">
            <div className="admin-modal-header"><div><h3>Edit roles</h3><p>{user.full_name} · {user.email}</p></div><button type="button" onClick={onClose}><X size={17} /></button></div>
            <div className="admin-modal-body">
                <div className="admin-modal-user"><div className="admin-avatar large">{getInitials(user.full_name)}</div><div><strong>{user.full_name}</strong><span>{formatOrganization(user.organization)}</span></div></div>
                <div className="admin-modal-section"><div className="admin-section-label"><span>Roles</span><small>{roles.length} selected</small></div><div className="admin-role-grid">{AVAILABLE_ROLES.map((role) => <label className={`admin-role-option ${roles.includes(role) ? "selected" : ""}`} key={role}><input type="checkbox" checked={roles.includes(role)} onChange={() => toggle(role)} /><span className="admin-role-check"><ShieldCheck size={14} /></span>{role}</label>)}</div></div>
                <div className="admin-role-help">{roles.map((role) => <div key={role}><strong>{role}</strong><span>{roleDescriptions[role]}</span></div>)}</div>
                <div className="admin-modal-section"><div className="admin-section-label"><span>Reporting manager</span><small>{managerRequired ? "Required" : "Not required"}</small></div><label className={`admin-select ${!managerRequired ? "disabled" : ""}`}><Users size={15} /><select value={managerId ?? ""} onChange={(e) => setManagerId(e.target.value ? Number(e.target.value) : null)} disabled={loadingCandidates || !managerRequired}>{!managerRequired && <option value="">No Manager</option>}{managerRequired && <option value="">Select manager</option>}{candidates.map((candidate) => <option key={candidate.user_id} value={candidate.user_id}>{candidate.full_name} — {candidate.email}</option>)}</select><ChevronDown size={14} /></label>{candidateError && <div className="admin-inline-error">{candidateError}</div>}</div>
                <div className="admin-modal-actions"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button onClick={save} disabled={saving || loadingCandidates}>{saving ? "Saving…" : "Save changes"}</Button></div>
            </div>
        </div>
    </div>;
}

function AdminLoading({ label }) { return <div className="admin-loading"><span className="admin-spinner" />{label}</div>; }
function getInitials(name) { return String(name || "U").trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase(); }
function formatOrganization(value) { return value ? value.replaceAll("_", " ").replace("PRE SALES TECHNICAL", "Pre-Sales / Technical").replace("ADMINISTRATION", "Administration").replace("SALES", "Sales") : "—"; }
