import { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, Clock3, RefreshCw, Search, XCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getEligibleSalesOwners, getSalesManagerReviewQueue, reviewOpportunity } from "../api/opportunityApi";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import StageBadge from "../components/ui/StageBadge";
import StatusBadge from "../components/ui/StatusBadge";

const money = (value) => {
    const number = Number(value || 0);
    if (number >= 1000000) return `$${(number / 1000000).toFixed(1)}M`;
    if (number >= 1000) return `$${(number / 1000).toFixed(0)}K`;
    return `$${number.toLocaleString()}`;
};

export default function SalesManagerReview() {
    const navigate = useNavigate();
    const [queue, setQueue] = useState([]);
    const [owners, setOwners] = useState([]);
    const [selection, setSelection] = useState({});
    const [search, setSearch] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(null);

    const load = async () => {
        try {
            setError("");
            const [items, candidates] = await Promise.all([getSalesManagerReviewQueue(), getEligibleSalesOwners()]);
            setQueue(items);
            setOwners(candidates);
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load review queue.");
        }
    };
    useEffect(() => { load(); }, []);

    const filtered = useMemo(() => queue.filter((o) => `${o.opportunity_name} ${o.created_by_user?.full_name || ""} ${o.account_id}`.toLowerCase().includes(search.toLowerCase())), [queue, search]);
    const update = (id, patch) => setSelection((p) => ({ ...p, [id]: { ...p[id], ...patch } }));

    const approve = async (opportunity) => {
        const ownerId = selection[opportunity.opportunity_id]?.ownerId;
        if (!ownerId) return setError("Select a Sales Executive before approving.");
        try {
            setBusy(opportunity.opportunity_id);
            setError("");
            await reviewOpportunity(opportunity.opportunity_id, { decision: "APPROVE", sales_owner_id: Number(ownerId), updated_at: opportunity.updated_at });
            await load();
        } catch (err) { setError(err?.response?.data?.message || "Approval failed."); }
        finally { setBusy(null); }
    };

    const reject = async (opportunity) => {
        const reason = selection[opportunity.opportunity_id]?.reason?.trim();
        if (!reason) return setError("A rejection reason is required.");
        if (!window.confirm("Reject this opportunity? The decision is final.")) return;
        try {
            setBusy(opportunity.opportunity_id);
            setError("");
            await reviewOpportunity(opportunity.opportunity_id, { decision: "REJECT", reason, updated_at: opportunity.updated_at });
            await load();
        } catch (err) { setError(err?.response?.data?.message || "Rejection failed."); }
        finally { setBusy(null); }
    };

    const totalValue = queue.reduce((sum, o) => sum + Number(o.estimated_value || 0), 0);

    return <div className="standard-page manager-review-page">
        <PageHeader title="Review Queue" description="Review submitted opportunities, validate ownership, and make the final sales decision." actions={<Button variant="secondary" onClick={load}><RefreshCw size={14} /> Refresh</Button>} />
        {error && <div className="standard-error">{error}</div>}
        <div className="manager-review-summary"><div><Clock3 size={18} /><span>Awaiting review</span><strong>{queue.length}</strong></div><div><span>Queue value</span><strong>{money(totalValue)}</strong></div><div><CheckCircle2 size={18} /><span>Sales owners</span><strong>{owners.length}</strong></div></div>
        <Card padding={false}>
            <div className="manager-review-toolbar"><div className="ui-search"><Search size={15} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search opportunity, creator or account…" /></div></div>
            <div className="manager-review-list">
                {filtered.map((opportunity) => {
                    const state = selection[opportunity.opportunity_id] || {};
                    const isBusy = busy === opportunity.opportunity_id;
                    return <article className="manager-review-card" key={opportunity.opportunity_id}>
                        <div className="manager-review-card-head"><div><div className="manager-review-title-row"><h2>{opportunity.opportunity_name}</h2><StatusBadge status={opportunity.status} /></div><p>{opportunity.created_by_user?.full_name || "Unknown creator"} · Account #{opportunity.account_id}</p></div><div className="record-meta"><StageBadge stage={opportunity.current_stage?.stage_name} /><strong className="manager-review-value">{money(opportunity.estimated_value)}</strong></div></div>
                        <div className="manager-review-stats"><div><span>Probability</span><strong>{opportunity.probability ?? 0}%</strong></div><div><span>Expected close</span><strong>{opportunity.expected_close_date || "—"}</strong></div><div><span>Submitted</span><strong>{opportunity.updated_at ? new Date(opportunity.updated_at).toLocaleDateString() : "—"}</strong></div></div>
                        <p className="manager-review-description">{opportunity.description || "No description provided."}</p>
                        <div className="manager-review-controls"><label className="field-label">Sales Owner<select value={state.ownerId || ""} onChange={(e) => update(opportunity.opportunity_id, { ownerId: e.target.value })}><option value="">Select Sales Executive</option>{owners.map((owner) => <option key={owner.user_id} value={owner.user_id}>{owner.full_name}</option>)}</select></label><label className="field-label">Rejection reason<textarea rows={2} placeholder="Required only when rejecting" value={state.reason || ""} onChange={(e) => update(opportunity.opportunity_id, { reason: e.target.value })} /></label></div>
                        <div className="manager-review-actions"><Button variant="ghost" onClick={() => navigate(`/opportunity/${opportunity.opportunity_id}`)}>Open opportunity <ArrowRight size={14} /></Button><div><Button variant="danger" disabled={isBusy} onClick={() => reject(opportunity)}><XCircle size={14} /> Reject</Button><Button disabled={isBusy} onClick={() => approve(opportunity)}><CheckCircle2 size={14} /> {isBusy ? "Saving…" : "Approve & assign"}</Button></div></div>
                    </article>;
                })}
                {!filtered.length && <div className="manager-empty"><EmptyState message={queue.length ? "No review items match your search." : "No opportunities awaiting review."} /></div>}
            </div>
        </Card>
    </div>;
}
