import { useEffect, useMemo, useState } from "react";
import { Building2, RefreshCw, Plus, Pencil, Trash2, X, Save } from "lucide-react";
import api from "../api/axiosClient";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import SearchInput from "../components/ui/SearchInput";
import EmptyState from "../components/ui/EmptyState";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import StatusBadge from "../components/ui/StatusBadge";
import FormSection from "../components/ui/FormSection";
import FormActions from "../components/ui/FormActions";
import "./OemRegistry.css";

const EMPTY_FORM = { partner_name: "", product_name: "", account_id: "", contact_person: "", email: "", phone: "", status: "Active", notes: "" };

export default function OemRegistry() {
    const { activeRole } = useAuth();
    const [rows, setRows] = useState([]);
    const [query, setQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("All");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [form, setForm] = useState(EMPTY_FORM);
    const leadership = activeRole === ROLES.LEADERSHIP;

    const load = async () => {
        try {
            setLoading(true);
            setError("");
            const response = await api.get("/oem/");
            setRows(Array.isArray(response.data) ? response.data : []);
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to load OEMs.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, [activeRole]);

    const statuses = useMemo(() => ["All", ...new Set(rows.map((row) => row.status).filter(Boolean).sort())], [rows]);
    const visible = useMemo(() => {
        const needle = query.trim().toLowerCase();
        return rows.filter((row) => {
            const matchesQuery = [row.partner_name, row.product_name, row.account_id, row.contact_person, row.email]
                .some((value) => String(value ?? "").toLowerCase().includes(needle));
            return matchesQuery && (statusFilter === "All" || row.status === statusFilter);
        });
    }, [rows, query, statusFilter]);

    const openCreate = () => {
        setEditingId(null);
        setForm({ ...EMPTY_FORM });
        setShowForm(true);
        setError("");
    };
    const openEdit = (row) => {
        setEditingId(row.oem_partner_id);
        setForm({ ...EMPTY_FORM, ...row, account_id: row.account_id == null ? "" : String(row.account_id) });
        setShowForm(true);
        setError("");
    };
    const closeForm = () => { setShowForm(false); setEditingId(null); setForm({ ...EMPTY_FORM }); };

    const submit = async (event) => {
        event.preventDefault();
        if (saving) return;
        try {
            setSaving(true);
            setError("");
            const payload = { ...form, account_id: form.account_id ? Number(form.account_id) : undefined };
            if (editingId != null) await api.put(`/oem/${editingId}`, payload);
            else await api.post("/oem/", payload);
            closeForm();
            await load();
        } catch (err) {
            setError(err?.response?.data?.message || `Unable to ${editingId != null ? "update" : "create"} OEM.`);
        } finally {
            setSaving(false);
        }
    };

    const remove = async (row) => {
        if (!window.confirm(`Delete OEM "${row.partner_name}"? OEMs referenced by opportunities cannot be deleted.`)) return;
        try {
            setError("");
            await api.delete(`/oem/${row.oem_partner_id}`);
            await load();
        } catch (err) {
            setError(err?.response?.data?.message || "Unable to delete OEM.");
        }
    };

    return (
        <div className="standard-page oem-registry-page">
            <PageHeader
                title="OEM Registry"
                description={leadership ? "Manage OEM partners, products, and master data." : "Browse OEM partners and products associated with the Deal Room."}
                actions={<>
                    <Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={14} />Refresh</Button>
                    {leadership && <Button onClick={openCreate}><Plus size={14} />Add OEM</Button>}
                </>}
            />

            {error && <ErrorState message={error} onRetry={load} />}

            {showForm && leadership && (
                <Card className="oem-form-card">
                    <div className="oem-form-heading">
                        <div><h2>{editingId != null ? "Edit OEM" : "Add OEM"}</h2><p>Maintain OEM and product information.</p></div>
                        <Button variant="ghost" onClick={closeForm} disabled={saving}><X size={15} />Close</Button>
                    </div>
                    <form className="oem-form" onSubmit={submit}>
                        <FormSection title="OEM information" description="Maintain partner, product, and account details.">
                            <div className="field-grid">
                                <label className="shared-form-field"><span>OEM name <span className="required-mark">*</span></span><input required maxLength={150} value={form.partner_name} onChange={(e) => setForm({ ...form, partner_name: e.target.value })} /></label>
                                <label className="shared-form-field"><span>Product <span className="required-mark">*</span></span><input required maxLength={150} value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })} /></label>
                                <label className="shared-form-field"><span>Account ID (optional)</span><input inputMode="numeric" value={form.account_id} onChange={(e) => setForm({ ...form, account_id: e.target.value.replace(/\D/g, "") })} placeholder="Uses default account when blank" /></label>
                                <label className="shared-form-field"><span>Contact person <span className="required-mark">*</span></span><input required maxLength={150} value={form.contact_person || ""} onChange={(e) => setForm({ ...form, contact_person: e.target.value.replace(/[^A-Za-z .'-]/g, "") })} /></label>
                                <label className="shared-form-field"><span>Email</span><input type="email" maxLength={150} value={form.email || ""} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
                                <label className="shared-form-field"><span>Phone</span><input type="tel" inputMode="numeric" maxLength={10} pattern="[0-9]{10}" value={form.phone || ""} onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/\D/g, "").slice(0, 10) })} placeholder="10-digit phone number" /></label>
                                <label className="shared-form-field"><span>Status</span><select value={form.status || "Active"} onChange={(e) => setForm({ ...form, status: e.target.value })}><option>Active</option><option>Inactive</option></select></label>
                                <label className="shared-form-field oem-notes-field"><span>Notes</span><textarea rows={3} value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
                            </div>
                        </FormSection>
                        <FormActions className="oem-form-actions"><Button variant="secondary" type="button" onClick={closeForm} disabled={saving}>Cancel</Button><Button type="submit" disabled={saving}>{saving ? "Saving…" : <><Save size={14} />{editingId != null ? "Save changes" : "Create OEM"}</>}</Button></FormActions>
                    </form>
                </Card>
            )}

            <Card padding={false} className="oem-table-card">
                <div className="oem-toolbar">
                    <SearchInput value={query} onChange={setQuery} placeholder="Search OEM, product, account…" />
                    <div className="oem-status-filters" role="group" aria-label="Filter OEMs by status">
                        {statuses.map((status) => <button key={status} type="button" className={statusFilter === status ? "active" : ""} onClick={() => setStatusFilter(status)}>{status}</button>)}
                    </div>
                    <span className="oem-result-count">{visible.length} of {rows.length}</span>
                </div>
                {loading ? <LoadingState message="Loading OEM registry…" /> : visible.length === 0 ? (
                    <EmptyState message={query || statusFilter !== "All" ? "No OEMs match your search or filter." : "No OEM partners found."} />
                ) : (
                    <div className="ui-table-wrap oem-table-wrap">
                        <table className="ui-data-table oem-table">
                            <thead><tr><th>OEM Partner</th><th>Product</th><th>Account</th><th>Status</th>{leadership && <th>Contact</th>}{leadership && <th className="oem-actions-heading">Actions</th>}</tr></thead>
                            <tbody>{visible.map((row) => <tr key={row.oem_partner_id}>
                                <td><div className="oem-name-cell"><span className="oem-icon"><Building2 size={17} /></span><div><strong>{row.partner_name}</strong><small>OEM #{row.oem_partner_id}</small></div></div></td>
                                <td>{row.product_name || "—"}</td>
                                <td>{row.account_id ? `Account #${row.account_id}` : "—"}</td>
                                <td><StatusBadge status={row.status} /></td>
                                {leadership && <td><div className="oem-contact-cell"><strong>{row.contact_person || "No contact"}</strong><small>{row.email || "—"}{row.phone ? ` · ${row.phone}` : ""}</small></div></td>}
                                {leadership && <td><div className="oem-row-actions"><Button size="sm" variant="secondary" onClick={() => openEdit(row)}><Pencil size={13} />Edit</Button><Button size="sm" variant="ghost" onClick={() => remove(row)}><Trash2 size={13} />Delete</Button></div></td>}
                            </tr>)}</tbody>
                        </table>
                    </div>
                )}
            </Card>
        </div>
    );
}
