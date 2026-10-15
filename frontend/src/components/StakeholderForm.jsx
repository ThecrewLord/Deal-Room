
import { useState, useEffect, useRef } from "react";
import { createStakeholder } from "../api/stakeholderApi";
import { getTags } from "../api/phase2Api";
import Button from "./ui/Button";
import FormSection from "./ui/FormSection";
import FormActions from "./ui/FormActions";
import "./StakeholderForm.css";

const DEFAULT_TAGS = [
    "Economic Buyer",
    "Technical Champion",
    "End User",
    "Blocker",
    "Decision Maker",
    "Other",
];

const EMPTY_FORM = {
    name: "",
    job_title: "",
    email: "",
    phone: "",
    tags: [],
};

const roleClass = (tag) =>
    `role-chip role-chip--${tag.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;

export default function StakeholderForm({ opportunityId, onCreated }) {
    const [form, setForm] = useState(EMPTY_FORM);
    const [tags, setTags] = useState(DEFAULT_TAGS);
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const dropdownRef = useRef(null);
    const searchRef = useRef(null);

    useEffect(() => {
        let active = true;

        getTags()
            .then((items) => {
                if (active && Array.isArray(items) && items.length) {
                    setTags([
                        ...new Set([
                            ...DEFAULT_TAGS,
                            ...items.map((item) => item.name).filter(Boolean),
                        ]),
                    ]);
                }
            })
            .catch(() => {});

        return () => {
            active = false;
        };
    }, []);

    useEffect(() => {
        if (!open) return;

        const onPointerDown = (event) => {
            if (!dropdownRef.current?.contains(event.target)) {
                setOpen(false);
                setSearch("");
            }
        };

        const onKeyDown = (event) => {
            if (event.key === "Escape") {
                setOpen(false);
                setSearch("");
            }
        };

        document.addEventListener("mousedown", onPointerDown);
        document.addEventListener("keydown", onKeyDown);

        return () => {
            document.removeEventListener("mousedown", onPointerDown);
            document.removeEventListener("keydown", onKeyDown);
        };
    }, [open]);

    useEffect(() => {
        if (open) searchRef.current?.focus();
    }, [open]);

    const toggle = (tag) => {
        setForm((current) => ({
            ...current,
            tags: current.tags.includes(tag)
                ? current.tags.filter((item) => item !== tag)
                : [...current.tags, tag],
        }));
    };

    const updateField = (field, value) => {
        setForm((current) => ({ ...current, [field]: value }));
    };

    const submit = async (event) => {
        event.preventDefault();
        if (submitting) return;

        setSubmitting(true);
        setError("");
        setSuccess("");

        try {
            await createStakeholder({
                ...form,
                opportunity_id: Number(opportunityId),
            });

            setForm({ ...EMPTY_FORM, tags: [] });
            setOpen(false);
            setSearch("");
            onCreated?.();
            setSuccess("Stakeholder added successfully.");
        } catch (err) {
            setError(
                err?.response?.data?.message ||
                    "Unable to save stakeholder. Please try again."
            );
        } finally {
            setSubmitting(false);
        }
    };

    const filteredTags = tags.filter((tag) =>
        tag.toLowerCase().includes(search.trim().toLowerCase())
    );

    return (
        <form onSubmit={submit} className="ui-form-grid stakeholder-form">
            {error && <div className="standard-error" role="alert">{error}</div>}
            {success && (
                <div className="standard-success" role="status">
                    ✓ {success}
                </div>
            )}
            <FormSection
                title="Stakeholder information"
                description="Add the contact and the roles they play in this opportunity."
            >
            <div className="field-grid">
            <label className="shared-form-field">
                <span>Name <span className="required-mark">*</span></span>
                <input required autoComplete="name" value={form.name} disabled={submitting}
                    onChange={(e) => updateField("name", e.target.value)} />
            </label>
            <label className="shared-form-field">
                <span>Job title</span>
                <input value={form.job_title} disabled={submitting}
                    onChange={(e) => updateField("job_title", e.target.value)} />
            </label>
            <label className="shared-form-field">
                <span>Email</span>
                <input type="email" autoComplete="email" value={form.email} disabled={submitting}
                    onChange={(e) => updateField("email", e.target.value)} />
            </label>
            <label className="shared-form-field">
                <span>Phone</span>
                <input type="tel" inputMode="numeric" maxLength={10} pattern="[0-9]{10}"
                    aria-describedby="stakeholder-phone-help" placeholder="10-digit phone number"
                    value={form.phone} disabled={submitting}
                    onChange={(e) => updateField("phone", e.target.value.replace(/\D/g, "").slice(0, 10))} />
                <small id="stakeholder-phone-help" className="shared-form-note">Enter 10 digits without a country code.</small>
            </label>

            <section className="role-field" ref={dropdownRef}>
                <div className="role-heading">
                    <label htmlFor="role-dropdown">Stakeholder roles</label>
                    <span>Optional · Select multiple</span>
                </div>

                <button
                    id="role-dropdown"
                    type="button"
                    className={`role-trigger ${open ? "is-open" : ""}`}
                    aria-expanded={open}
                    disabled={submitting}
                    onClick={() => setOpen((value) => !value)}
                >
                    <span>
                        {form.tags.length
                            ? `${form.tags.length} role${form.tags.length === 1 ? "" : "s"} selected`
                            : "Select stakeholder roles"}
                    </span>
                    <span className={`role-chevron ${open ? "rotated" : ""}`}>
                        ▾
                    </span>
                </button>

                {form.tags.length > 0 && (
                    <div className="role-selected">
                        {form.tags.map((tag) => (
                            <span className={roleClass(tag)} key={tag}>
                                {tag}
                                <button
                                    type="button"
                                    aria-label={`Remove ${tag}`}
                                    disabled={submitting}
                                    onClick={() => toggle(tag)}
                                >
                                    ×
                                </button>
                            </span>
                        ))}
                        <button
                            type="button"
                            className="role-clear"
                            onClick={() =>
                                setForm((current) => ({ ...current, tags: [] }))
                            }
                            disabled={submitting}
                        >
                            Clear all
                        </button>
                    </div>
                )}

                {open && (
                    <div className="role-menu">
                        <div className="role-search">
                            <span aria-hidden="true">⌕</span>
                            <input
                                ref={searchRef}
                                placeholder="Search roles..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                aria-label="Search stakeholder roles"
                            />
                        </div>

                        <div className="role-options">
                            {filteredTags.length ? (
                                filteredTags.map((tag) => {
                                    const selected = form.tags.includes(tag);

                                    return (
                                        <button
                                            type="button"
                                            key={tag}
                                            className={`role-option ${selected ? "selected" : ""}`}
                                            aria-pressed={selected}
                                            onClick={() => toggle(tag)}
                                        >
                                            <span className={`role-checkbox ${selected ? "checked" : ""}`}>
                                                {selected ? "✓" : ""}
                                            </span>
                                            <span>{tag}</span>
                                        </button>
                                    );
                                })
                            ) : (
                                <p className="role-empty">No matching roles found.</p>
                            )}
                        </div>

                        <div className="role-footer">
                            <span>{form.tags.length} selected</span>
                            <button
                                type="button"
                                onClick={() => {
                                    setOpen(false);
                                    setSearch("");
                                }}
                            >
                                Done
                            </button>
                        </div>
                    </div>
                )}
            </section>
            </div>
            </FormSection>

            <FormActions className="role-submit">
                <Button type="submit" disabled={submitting}>
                    {submitting ? "Saving stakeholder…" : "Add stakeholder"}
                </Button>
            </FormActions>
        </form>
    );
}
