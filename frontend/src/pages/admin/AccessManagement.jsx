import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Filter, KeyRound, Mail, RefreshCw, Search, ShieldAlert, ShieldCheck, UserX, X } from "lucide-react";
import adminApi from "../../api/adminApi";
import { useAuth } from "../../context/AuthContext";
import "../../styles/admin.css";
import PageHeader from "../../components/ui/PageHeader";
import Button from "../../components/ui/Button";
import StatusBadge from "../../components/ui/StatusBadge";

export default function AccessManagement() {
    const { user: currentUser } = useAuth();
    const [users, setUsers] = useState([]);
    const [filter, setFilter] = useState("ALL");
    const [search, setSearch] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const load = async ({ refresh = false } = {}) => {
        try {
            refresh ? setRefreshing(true) : setLoading(true);
            setError("");
            setUsers(await adminApi.getUsers());
        } catch (e) { setError(e?.response?.data?.message || "Unable to load access records."); }
        finally { setLoading(false); setRefreshing(false); }
    };
    useEffect(() => { load(); }, []);

    const revoke = async (user) => {
        if (!window.confirm(`Revoke access for ${user.full_name}?`)) return;
        try {
            setError(""); setSuccess("");
            await adminApi.revoke(user.user_id);
            setSuccess(`Access revoked for ${user.full_name}.`);
            await load();
        } catch (e) { setError(e?.response?.data?.message || "Unable to revoke access."); }
    };

    const stats = useMemo(() => ({
        approved: users.filter((u) => u.status === "APPROVED" && u.active).length,
        pending: users.filter((u) => u.status === "PENDING").length,
        revoked: users.filter((u) => u.status === "REVOKED").length,
        inactive: users.filter((u) => u.status === "APPROVED" && !u.active).length,
    }), [users]);

    const visible = useMemo(() => {
        const query = search.trim().toLowerCase();
        return users.filter((u) => {
            const matchesStatus = filter === "ALL" || u.status === filter;
            const matchesSearch = !query || u.full_name?.toLowerCase().includes(query) || u.email?.toLowerCase().includes(query);
            return matchesStatus && matchesSearch;
        });
    }, [users, filter, search]);

    return <div className="standard-page admin-page">
        <PageHeader title="Access Management" description="Monitor account access, identify blocked users and revoke active access when necessary."
            actions={<Button variant="secondary" onClick={() => load({ refresh: true })} disabled={refreshing}><RefreshCw size={14} className={refreshing ? "admin-spin" : ""} /> Refresh</Button>} />

        <div className="admin-access-banner"><div className="admin-access-banner-icon"><KeyRound size={20} /></div><div><strong>Access control center</strong><span>Only approved and active users can access the Deal Room workspace.</span></div></div>

        <div className="admin-stat-grid">
            <AccessStat icon={ShieldCheck} label="Active access" value={stats.approved} tone="success" />
            <AccessStat icon={ShieldAlert} label="Pending" value={stats.pending} tone="warning" />
            <AccessStat icon={UserX} label="Revoked" value={stats.revoked} tone="danger" />
            <AccessStat icon={KeyRound} label="Inactive" value={stats.inactive} />
        </div>

        {error && <div className="admin-alert admin-alert-error"><span>{error}</span></div>}
        {success && <div className="admin-alert admin-alert-success"><CheckCircle2 size={16} /><span>{success}</span></div>}

        <div className="admin-toolbar-panel">
            <div className="admin-search"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search users by name or email…" />{search && <button type="button" onClick={() => setSearch("")}><X size={14} /></button>}</div>
            <div className="admin-filter"><Filter size={15} /><select value={filter} onChange={(e) => setFilter(e.target.value)}><option value="ALL">All access states</option><option value="APPROVED">Approved</option><option value="PENDING">Pending</option><option value="REVOKED">Revoked</option></select></div>
            <span className="admin-result-count">{visible.length} accounts</span>
        </div>

        {loading ? <div className="admin-card"><AdminLoading label="Loading access records…" /></div> : <div className="admin-table-card"><div className="admin-table-wrap">
            <table className="admin-table enhanced">
                <thead><tr><th>User</th><th>Access status</th><th>Roles</th><th>Manager</th><th>Access state</th><th>Action</th></tr></thead>
                <tbody>{visible.length === 0 ? <tr><td colSpan="6"><div className="admin-table-empty"><Search size={20} /><strong>No matching accounts</strong><span>Try another search or access state.</span></div></td></tr> : visible.map((u) => <tr key={u.user_id}>
                    <td><div className="admin-table-user"><div className="admin-avatar">{getInitials(u.full_name)}</div><div><strong>{u.full_name}</strong><span><Mail size={11} />{u.email}</span></div></div></td>
                    <td><StatusBadge status={u.status} /></td>
                    <td><div className="role-chips">{(u.roles || []).map((role) => <span className="role-chip" key={role}>{role}</span>)}</div></td>
                    <td>{u.manager_name || <span className="muted">No manager</span>}</td>
                    <td><div className="access-state"><span className={`access-dot ${String(u.status).toLowerCase()}`} /><span>{u.active ? "Active access" : "Not active"}</span></div></td>
                    <td>{u.status === "APPROVED" && u.user_id !== currentUser?.user_id ? <Button size="sm" variant="danger" onClick={() => revoke(u)}><UserX size={12} /> Revoke</Button> : <span className="muted">{u.user_id === currentUser?.user_id ? "Your account" : "No action"}</span>}</td>
                </tr>)}</tbody>
            </table>
        </div></div>}
    </div>;
}
function AccessStat({ icon: Icon, label, value, tone = "" }) { return <div className="admin-access-stat"><span className={`admin-access-icon ${tone}`}><Icon size={17} /></span><div><strong>{value}</strong><small>{label}</small></div></div>; }
function AdminLoading({ label }) { return <div className="admin-loading"><span className="admin-spinner" />{label}</div>; }
function getInitials(name) { return String(name || "U").trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase(); }
