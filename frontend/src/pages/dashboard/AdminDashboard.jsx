import {
    ArrowRight,
    CheckCircle2,
    Clock3,
    ShieldCheck,
    UserCheck,
    UserCog,
    Users,
    UserX,
    RefreshCw,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import adminApi from "../../api/adminApi";
import { useAuth } from "../../context/AuthContext";

const ROLE_LABELS = [
    "Admin",
    "Sales Manager",
    "Pre-Sales Manager",
    "Sales Executive",
    "Solution Engineer",
    "Solution Engineer",
];

const roleShortName = (role) => {
    const map = {
        "Sales Manager": "Sales Managers",
        "Pre-Sales Manager": "Pre-Sales Managers",
        "Sales Executive": "Sales Executives",
        "Solution Engineer": "Solution Engineers",
        
        Admin: "Admins",
    };
    return map[role] || role;
};

const formatDate = (value) => {
    if (!value) return "Never";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";
    return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
};

function AdminKpi({ label, value, helper, icon: Icon, tone = "blue" }) {
    return (
        <article className={`admin-dashboard-kpi admin-dashboard-kpi-${tone}`}>
            <div className="admin-dashboard-kpi-top">
                <span>{label}</span>
                <div className="admin-dashboard-kpi-icon"><Icon size={17} /></div>
            </div>
            <strong>{value}</strong>
            <small>{helper}</small>
        </article>
    );
}

function AdminCard({ title, description, action, children, className = "" }) {
    return (
        <section className={`admin-dashboard-card ${className}`}>
            <div className="admin-dashboard-card-header">
                <div>
                    <h2>{title}</h2>
                    {description && <p>{description}</p>}
                </div>
                {action}
            </div>
            {children}
        </section>
    );
}

export default function AdminDashboard() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [users, setUsers] = useState([]);
    const [pending, setPending] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState("");

    const loadData = async ({ refresh = false } = {}) => {
        try {
            refresh ? setRefreshing(true) : setLoading(true);
            setError("");
            const [allUsers, pendingUsers] = await Promise.all([
                adminApi.getUsers(),
                adminApi.getPending(),
            ]);
            setUsers(Array.isArray(allUsers) ? allUsers : []);
            setPending(Array.isArray(pendingUsers) ? pendingUsers : []);
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load administration data.");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const stats = useMemo(() => {
        const approved = users.filter((item) => item.status === "APPROVED");
        const revoked = users.filter((item) => item.status === "REVOKED");
        return {
            total: users.length,
            active: approved.filter((item) => item.active).length,
            pending: pending.length,
            revoked: revoked.length,
        };
    }, [users, pending]);

    const roleDistribution = useMemo(() => {
        return ROLE_LABELS.map((role) => ({
            role,
            count: users.filter((item) => (item.roles || []).includes(role)).length,
        })).filter((item) => item.count > 0);
    }, [users]);

    const recentUsers = users.slice(0, 5);

    if (loading) {
        return (
            <div className="admin-dashboard">
                <div className="admin-dashboard-loading">
                    <div className="admin-dashboard-spinner" />
                    <span>Loading administration overview…</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="admin-dashboard">
                <div className="admin-dashboard-error">
                    <div className="admin-dashboard-error-icon"><ShieldCheck size={20} /></div>
                    <div>
                        <h2>Administration data unavailable</h2>
                        <p>{error}</p>
                    </div>
                    <button className="ui-button ui-button-md ui-button-primary" onClick={() => loadData()}>
                        Try again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard">
            <header className="admin-dashboard-hero">
                <div>
                    <div className="admin-dashboard-eyebrow">
                        <ShieldCheck size={14} /> Administration
                    </div>
                    <h1>Good to see you, {user?.full_name?.split(" ")[0] || "Admin"}.</h1>
                    <p>Manage users, roles and platform access from one place.</p>
                </div>
                <button
                    className="ui-button ui-button-md ui-button-secondary admin-dashboard-refresh"
                    onClick={() => loadData({ refresh: true })}
                    disabled={refreshing}
                >
                    <RefreshCw size={14} className={refreshing ? "admin-dashboard-spin" : ""} />
                    Refresh
                </button>
            </header>

            <div className="admin-dashboard-kpi-grid">
                <AdminKpi label="Total users" value={stats.total} helper="All registered accounts" icon={Users} />
                <AdminKpi label="Active users" value={stats.active} helper="Approved and enabled" icon={UserCheck} tone="green" />
                <AdminKpi label="Pending approvals" value={stats.pending} helper="Require administrator review" icon={Clock3} tone="orange" />
                <AdminKpi label="Revoked access" value={stats.revoked} helper="Accounts currently blocked" icon={UserX} tone="red" />
            </div>

            <div className="admin-dashboard-main-grid">
                <AdminCard
                    title="Pending approvals"
                    description="Users waiting for access to be reviewed."
                    action={
                        <button className="admin-dashboard-text-button" onClick={() => navigate("/admin/approval")}>
                            View all <ArrowRight size={14} />
                        </button>
                    }
                    className="admin-dashboard-pending"
                >
                    {pending.length === 0 ? (
                        <div className="admin-dashboard-empty">
                            <div className="admin-dashboard-empty-icon"><CheckCircle2 size={19} /></div>
                            <strong>All caught up</strong>
                            <span>There are no pending access requests.</span>
                        </div>
                    ) : (
                        <div className="admin-dashboard-list">
                            {pending.slice(0, 4).map((item) => (
                                <button key={item.user_id} className="admin-dashboard-user-row" onClick={() => navigate("/admin/approval")}>
                                    <div className="admin-dashboard-avatar">{getInitials(item.full_name)}</div>
                                    <div className="admin-dashboard-user-main">
                                        <strong>{item.full_name}</strong>
                                        <span>{item.email}</span>
                                    </div>
                                    <span className="admin-dashboard-status pending">Pending</span>
                                    <ArrowRight size={15} className="admin-dashboard-row-arrow" />
                                </button>
                            ))}
                        </div>
                    )}
                </AdminCard>

                <AdminCard title="Quick actions" description="Jump directly to an administration task.">
                    <div className="admin-dashboard-actions">
                        <button onClick={() => navigate("/admin/approval")}>
                            <span className="admin-dashboard-action-icon orange"><Clock3 size={17} /></span>
                            <span><strong>Review approvals</strong><small>Process pending requests</small></span>
                            <ArrowRight size={15} />
                        </button>
                        <button onClick={() => navigate("/admin/users")}>
                            <span className="admin-dashboard-action-icon blue"><Users size={17} /></span>
                            <span><strong>Manage users</strong><small>View and update accounts</small></span>
                            <ArrowRight size={15} />
                        </button>
                        <button onClick={() => navigate("/admin/roles")}>
                            <span className="admin-dashboard-action-icon purple"><UserCog size={17} /></span>
                            <span><strong>Manage roles</strong><small>Configure user responsibilities</small></span>
                            <ArrowRight size={15} />
                        </button>
                        <button onClick={() => navigate("/admin/access")}>
                            <span className="admin-dashboard-action-icon green"><ShieldCheck size={17} /></span>
                            <span><strong>Manage access</strong><small>Review account status</small></span>
                            <ArrowRight size={15} />
                        </button>
                    </div>
                </AdminCard>
            </div>

            <div className="admin-dashboard-secondary-grid">
                <AdminCard title="Role distribution" description="Users assigned to each platform role.">
                    <div className="admin-dashboard-role-list">
                        {roleDistribution.length === 0 ? (
                            <div className="admin-dashboard-muted">No role assignments yet.</div>
                        ) : roleDistribution.map((item) => (
                            <div className="admin-dashboard-role-row" key={item.role}>
                                <span className="admin-dashboard-role-dot" />
                                <span>{roleShortName(item.role)}</span>
                                <strong>{item.count}</strong>
                            </div>
                        ))}
                    </div>
                </AdminCard>

                <AdminCard title="Recent users" description="Latest accounts added to the platform." action={<button className="admin-dashboard-text-button" onClick={() => navigate("/admin/users")}>Manage users <ArrowRight size={14} /></button>}>
                    <div className="admin-dashboard-list admin-dashboard-recent-list">
                        {recentUsers.length === 0 ? (
                            <div className="admin-dashboard-muted">No users found.</div>
                        ) : recentUsers.map((item) => (
                            <div className="admin-dashboard-recent-row" key={item.user_id}>
                                <div className="admin-dashboard-avatar">{getInitials(item.full_name)}</div>
                                <div className="admin-dashboard-user-main">
                                    <strong>{item.full_name}</strong>
                                    <span>{item.email}</span>
                                </div>
                                <div className="admin-dashboard-recent-meta">
                                    <span className={`admin-dashboard-status ${String(item.status || "").toLowerCase()}`}>{titleCase(item.status)}</span>
                                    <small>{formatDate(item.created_at)}</small>
                                </div>
                            </div>
                        ))}
                    </div>
                </AdminCard>
            </div>
        </div>
    );
}

function getInitials(name) {
    return String(name || "U")
        .trim()
        .split(/\s+/)
        .map((part) => part[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();
}

function titleCase(value) {
    return String(value || "Unknown")
        .toLowerCase()
        .replace(/_/g, " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
