import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, Clock3, Mail, RefreshCw, ShieldCheck, UserCheck, Users, XCircle } from "lucide-react";
import adminApi from "../../api/adminApi";
import { AVAILABLE_ROLES, ROLES } from "../../auth/roles";
import Button from "../../components/ui/Button";
import PageHeader from "../../components/ui/PageHeader";
import StatusBadge from "../../components/ui/StatusBadge";

const MANAGED_ROLES = new Set([ROLES.SALES_EXECUTIVE, ROLES.SOLUTION_ENGINEER, ROLES.SOLUTION_ENGINEER]);

export default function UserApproval() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [busy, setBusy] = useState(null);

    const loadUsers = async ({ refresh = false } = {}) => {
        try {
            refresh ? setRefreshing(true) : setLoading(true);
            setError("");
            setUsers(await adminApi.getPending());
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load pending users.");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => { loadUsers(); }, []);

    const approve = async (user, roles, managerId) => {
        try {
            setBusy(user.user_id);
            setError("");
            setSuccess("");
            await adminApi.approve(user.user_id, roles, managerId);
            setSuccess(`${user.full_name} was approved successfully.`);
            await loadUsers();
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to approve user.");
        } finally {
            setBusy(null);
        }
    };

    return (
        <div className="standard-page admin-page">
            <PageHeader
                title="Pending Approvals"
                description="Review new access requests, assign final roles and connect users to the right manager."
                actions={
                    <Button variant="secondary" onClick={() => loadUsers({ refresh: true })} disabled={refreshing}>
                        <RefreshCw size={14} className={refreshing ? "admin-spin" : ""} />
                        Refresh
                    </Button>
                }
            />

            <div className="admin-summary-strip">
                <SummaryItem icon={Clock3} label="Waiting for review" value={users.length} tone="warning" />
                <SummaryItem icon={ShieldCheck} label="Approval policy" value="Role + manager" />
                <SummaryItem icon={UserCheck} label="Ready to approve" value={users.filter((u) => u.status === "PENDING").length} tone="success" />
            </div>

            {error && <div className="admin-alert admin-alert-error"><XCircle size={16} /><span>{error}</span></div>}
            {success && <div className="admin-alert admin-alert-success"><CheckCircle2 size={16} /><span>{success}</span></div>}

            {loading ? (
                <AdminLoading label="Loading pending access requests…" />
            ) : users.length === 0 ? (
                <div className="admin-empty-panel">
                    <div className="admin-empty-icon success"><CheckCircle2 size={22} /></div>
                    <h3>You're all caught up</h3>
                    <p>There are no pending access requests waiting for administrator review.</p>
                </div>
            ) : (
                <div className="admin-approval-stack">
                    {users.map((user) => (
                        <ApprovalCard key={user.user_id} user={user} busy={busy === user.user_id} onApprove={approve} />
                    ))}
                </div>
            )}
        </div>
    );
}

function ApprovalCard({ user, busy, onApprove }) {
    const [roles, setRoles] = useState([]);
    const [managerId, setManagerId] = useState(null);
    const [candidates, setCandidates] = useState([]);
    const [candidateLoading, setCandidateLoading] = useState(false);
    const [candidateError, setCandidateError] = useState("");

    const managerRequired = useMemo(
        () => roles.some((role) => MANAGED_ROLES.has(role)),
        [roles]
    );

    useEffect(() => {
        let mounted = true;
        setCandidateLoading(true);
        setCandidateError("");
        adminApi.getManagerCandidates(user.user_id, roles)
            .then((items) => mounted && setCandidates(items || []))
            .catch((err) => mounted && setCandidateError(err?.response?.data?.message || "Unable to load eligible managers."))
            .finally(() => mounted && setCandidateLoading(false));
        return () => { mounted = false; };
    }, [user.user_id, roles]);

    useEffect(() => {
        if (!managerRequired) setManagerId(null);
        else if (!candidates.some((candidate) => candidate.user_id === managerId)) setManagerId(null);
    }, [managerRequired, candidates, managerId]);

    const toggle = (role) => {
        setRoles((current) =>
            current.includes(role)
                ? current.filter((item) => item !== role)
                : [...current, role]
        );
    };

    const canApprove =
        roles.length > 0 &&
        (!managerRequired || !!managerId) &&
        !candidateLoading &&
        !candidateError;

    return (
        <section className="admin-request-card">
            <div className="admin-request-head">
                <div className="admin-user-identity">
                    <div className="admin-avatar large">{getInitials(user.full_name)}</div>
                    <div>
                        <div className="admin-identity-name">{user.full_name}</div>
                        <div className="admin-identity-email"><Mail size={13} /> {user.email}</div>
                    </div>
                </div>
                <StatusBadge status="PENDING" />
            </div>

            <div className="admin-request-body">
                <div className="admin-request-section">
                    <div className="admin-section-label">
                        <span>Assign roles</span>
                        <small>{roles.length} selected</small>
                    </div>
                    <div className="admin-role-grid">
                        {AVAILABLE_ROLES.map((role) => (
                            <label className={`admin-role-option ${roles.includes(role) ? "selected" : ""}`} key={role}>
                                <input type="checkbox" checked={roles.includes(role)} onChange={() => toggle(role)} />
                                <span className="admin-role-check"><CheckCircle2 size={15} /></span>
                                <span>{role}</span>
                            </label>
                        ))}
                    </div>
                </div>

                <div className="admin-request-section">
                    <div className="admin-section-label">
                        <span>Reporting manager</span>
                        <small>{managerRequired ? "Required for selected role" : "Optional"}</small>
                    </div>
                    <label className={`admin-select ${managerRequired ? "" : "disabled"}`}>
                        <Users size={15} />
                        <select
                            value={managerId ?? ""}
                            onChange={(e) => setManagerId(e.target.value ? Number(e.target.value) : null)}
                            disabled={candidateLoading || !managerRequired}
                        >
                            {!managerRequired && <option value="">No Manager required</option>}
                            {managerRequired && <option value="">Select an eligible manager</option>}
                            {candidates.map((candidate) => (
                                <option key={candidate.user_id} value={candidate.user_id}>
                                    {candidate.full_name} — {candidate.email}
                                </option>
                            ))}
                        </select>
                        <ChevronDown size={15} />
                    </label>
                    {candidateLoading && <div className="admin-inline-note">Finding eligible managers…</div>}
                    {candidateError && <div className="admin-inline-error">{candidateError}</div>}
                </div>
            </div>

            <div className="admin-request-footer">
                <div className="admin-request-hint">
                    <ShieldCheck size={15} />
                    <span>Approval grants the selected roles and platform access.</span>
                </div>
                <Button disabled={busy || !canApprove} onClick={() => onApprove(user, roles, managerId)}>
                    {busy ? "Approving…" : "Approve access"}
                </Button>
            </div>
        </section>
    );
}

function SummaryItem({ icon: Icon, label, value, tone = "" }) {
    return (
        <div className="admin-summary-item">
            <span className={`admin-summary-icon ${tone}`}><Icon size={16} /></span>
            <span><small>{label}</small><strong>{value}</strong></span>
        </div>
    );
}

function AdminLoading({ label }) {
    return <div className="admin-loading"><span className="admin-spinner" />{label}</div>;
}

function getInitials(name) {
    return String(name || "U").trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}
