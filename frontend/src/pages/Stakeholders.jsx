import "../styles/business-workspaces.css";
import { useEffect, useMemo, useState } from "react";
import { Mail, Phone, RefreshCw, Search, Target, Users, UserRound, BriefcaseBusiness } from "lucide-react";
import { getOpportunities } from "../api/opportunityApi";
import { getStakeholdersByOpportunity } from "../api/stakeholderApi";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import FilterToolbar from "../components/ui/FilterToolbar";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";
import StatusBadge from "../components/ui/StatusBadge";
import Button from "../components/ui/Button";

export default function Stakeholders() {
    const { activeRole } = useAuth();
    const [items, setItems] = useState([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        try {
            setLoading(true);
            setError("");
            const opportunities = await getOpportunities();
            const groups = await Promise.all(
                opportunities.map(async (opportunity) => {
                    const stakeholders = await getStakeholdersByOpportunity(opportunity.opportunity_id);
                    return stakeholders.map((stakeholder) => ({
                        ...stakeholder,
                        opportunity_name: opportunity.opportunity_name,
                        account_name: opportunity.account_name,
                    }));
                })
            );
            setItems(groups.flat());
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load stakeholders. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (activeRole === ROLES.SOLUTION_ENGINEER) load();
        else setLoading(false);
    }, [activeRole]);

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        return items.filter((item) => [
            item.stakeholder_name, item.designation, item.email, item.phone,
            item.influence_level, item.opportunity_name, item.account_name
        ].filter(Boolean).join(" ").toLowerCase().includes(q));
    }, [items, search]);

    const opportunities = new Set(items.map((item) => item.opportunity_id).filter(Boolean)).size;
    const decisionRoles = new Set(items.map((item) => item.influence_level).filter(Boolean)).size;

    if (activeRole !== ROLES.SOLUTION_ENGINEER) {
        return <div className="standard-page"><PageHeader title="Stakeholder Mapping" description="This workspace is available to Solution Engineers." /></div>;
    }

    return (
        <div className="standard-page business-workspace fade-in">
            <PageHeader
                title="Stakeholder Mapping"
                description="Map the people who influence technical decisions across your opportunities."
                actions={<Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={14} /> Refresh</Button>}
            />
            {error && <ErrorState message={error} onRetry={load} />}

            <div className="ui-kpi-grid">
                <KpiCard icon={Users} label="Stakeholders" value={items.length} description="Authorized contacts" />
                <KpiCard icon={Target} label="Opportunities" value={opportunities} description="Opportunities represented" />
                <KpiCard icon={UserRound} label="Decision Roles" value={decisionRoles} description="Influence levels represented" />
                <KpiCard icon={Search} label="Showing" value={visible.length} description="Current result set" />
            </div>

            <SectionCard title="Stakeholder Directory" description="Customer contacts linked to your authorized opportunities." icon={Users}>
                <FilterToolbar
                    search={{ icon: <Search size={14} />, value: search, onChange: (e) => setSearch(e.target.value) }}
                    placeholder="Search name, role, email, phone, account or opportunity…"
                    hasFilters={Boolean(search)}
                    onClear={() => setSearch("")}
                />
                {loading ? (
                    <LoadingState message="Loading stakeholders…" />
                ) : error ? null : !visible.length ? (
                    <EmptyState message={search ? "No stakeholders match your search." : "No stakeholders found for your authorized opportunities."} />
                ) : (
                    <div className="stakeholder-directory">
                        {visible.map((item) => (
                            <article className="stakeholder-directory-card" key={item.stakeholder_id}>
                                <div className="stakeholder-directory-avatar">
                                    {(item.stakeholder_name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}
                                </div>
                                <div className="stakeholder-directory-main">
                                    <div className="stakeholder-directory-title">
                                        <div className="ui-primary-cell">
                                            <strong>{item.stakeholder_name || "Unnamed stakeholder"}</strong>
                                            <span>{item.designation || "Designation not provided"}</span>
                                        </div>
                                        {item.influence_level && <StatusBadge status={item.influence_level} />}
                                    </div>
                                    <div className="stakeholder-directory-context">
                                        <span><BriefcaseBusiness size={13} />{item.account_name || "Account unavailable"}</span>
                                        <span><Target size={13} />{item.opportunity_name || "Opportunity unavailable"}</span>
                                    </div>
                                    <div className="stakeholder-directory-contact">
                                        {item.email && <a href={`mailto:${item.email}`}><Mail size={13} />{item.email}</a>}
                                        {item.phone && <a href={`tel:${item.phone}`}><Phone size={13} />{item.phone}</a>}
                                    </div>
                                    {item.notes && <p className="stakeholder-notes">{item.notes}</p>}
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </SectionCard>
        </div>
    );
}
