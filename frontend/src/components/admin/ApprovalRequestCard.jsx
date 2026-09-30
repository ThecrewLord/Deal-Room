import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, Mail, ShieldCheck, Users } from "lucide-react";
import adminApi from "../../api/adminApi";
import { AVAILABLE_ROLES, ROLES } from "../../auth/roles";
import Button from "../ui/Button";
import StatusBadge from "../ui/StatusBadge";

const MANAGED_ROLES = new Set([ROLES.SALES_EXECUTIVE, ROLES.SOLUTION_ENGINEER, ROLES.DEVOPS_ENGINEER, ROLES.DATA_ANALYST]);

export default function ApprovalRequestCard({ user, busy, onApprove, onError }) {
    const [roles, setRoles] = useState([]);
    const [managerId, setManagerId] = useState(null);
    const [candidates, setCandidates] = useState([]);
    const [candidateLoading, setCandidateLoading] = useState(false);
    const [candidateError, setCandidateError] = useState("");
    const managerRequired = useMemo(() => roles.some((role) => MANAGED_ROLES.has(role)), [roles]);

    useEffect(() => {
        let mounted = true;
        setCandidateLoading(true); setCandidateError("");
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

    const toggle = (role) => setRoles((current) => current.includes(role) ? current.filter((item) => item !== role) : [...current, role]);
    const canApprove = roles.length > 0 && (!managerRequired || !!managerId) && !candidateLoading && !candidateError;
    const approve = () => onApprove(user, roles, managerId);

    return <section className="admin-request-card">
        <div className="admin-request-head">
            <div className="admin-user-identity"><div className="admin-avatar large">{getInitials(user.full_name)}</div><div><div className="admin-identity-name">{user.full_name}</div><div className="admin-identity-email"><Mail size={13} /> {user.email}</div></div></div>
            <StatusBadge status="PENDING" />
        </div>
        <div className="admin-request-body">
            <div className="admin-request-section">
                <div className="admin-section-label"><span>Assign roles</span><small>{roles.length} selected</small></div>
                <div className="admin-role-grid">
                    {AVAILABLE_ROLES.filter((role) => role !== ROLES.LEADERSHIP).map((role) => <label className={`admin-role-option ${roles.includes(role) ? "selected" : ""}`} key={role}><input type="checkbox" checked={roles.includes(role)} onChange={() => toggle(role)} /><span className="admin-role-check"><CheckCircle2 size={15} /></span><span>{role}</span></label>)}
                </div>
            </div>
            <div className="admin-request-section">
                <div className="admin-section-label"><span>Reporting manager</span><small>{managerRequired ? "Required for selected role" : "Optional"}</small></div>
                <label className={`admin-select ${managerRequired ? "" : "disabled"}`}><Users size={15} /><select value={managerId ?? ""} onChange={(e) => setManagerId(e.target.value ? Number(e.target.value) : null)} disabled={candidateLoading || !managerRequired}>{!managerRequired && <option value="">No Manager required</option>}{managerRequired && <option value="">Select an eligible manager</option>}{candidates.map((candidate) => <option key={candidate.user_id} value={candidate.user_id}>{candidate.full_name} — {candidate.email}</option>)}</select><ChevronDown size={15} /></label>
                {candidateLoading && <div className="admin-inline-note">Finding eligible managers…</div>}
                {candidateError && <div className="admin-inline-error">{candidateError}</div>}
            </div>
        </div>
        <div className="admin-request-footer"><div className="admin-request-hint"><ShieldCheck size={15} /><span>Approval grants the selected roles and platform access.</span></div><Button disabled={busy || !canApprove} onClick={approve}>{busy ? "Approving…" : "Approve access"}</Button></div>
    </section>;
}

function getInitials(name) { return String(name || "U").trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase(); }
