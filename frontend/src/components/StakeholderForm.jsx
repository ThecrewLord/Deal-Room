import { useState } from "react";
import { createStakeholder } from "../api/stakeholderApi";
import { getTags } from "../api/phase2Api";
import Button from "./ui/Button";
import { useEffect } from "react";

const DEFAULT = [
    "Economic Buyer",
    "Technical Champion",
    "End User",
    "Blocker",
    "Decision Maker",
];

export default function StakeholderForm({
    opportunityId,
    companyName = "",
    onCreated,
}) {
    const [form, setForm] = useState({
        name: "",
        job_title: "",
        email: "",
        phone: "",
        company: companyName,
        tags: [],
    });

    const [tags, setTags] = useState(DEFAULT);
    const [error, setError] = useState("");

    useEffect(() => {
        getTags()
            .then((x) => setTags(x.map((t) => t.name)))
            .catch(() => {});
    }, []);

    useEffect(() => {
        setForm((current) => ({
            ...current,
            company: companyName || current.company,
        }));
    }, [companyName]);

    const submit = async (e) => {
        e.preventDefault();

        if (form.phone && form.phone.length !== 10) {
            setError("Phone number must contain exactly 10 digits.");
            return;
        }

        try {
            await createStakeholder({
                ...form,
                opportunity_id: Number(opportunityId),
            });

            setForm({
                name: "",
                job_title: "",
                email: "",
                phone: "",
                company: companyName,
                tags: [],
            });

            setError("");
            onCreated?.();
        } catch (x) {
            setError(
                x?.response?.data?.message ||
                "Unable to save stakeholder."
            );
        }
    };

    const toggle = (t) =>
        setForm((f) => ({
            ...f,
            tags: f.tags.includes(t)
                ? f.tags.filter((x) => x !== t)
                : [...f.tags, t],
        }));

    const handlePhoneChange = (e) => {
        const digitsOnly = e.target.value
            .replace(/\D/g, "")
            .slice(0, 10);

        setForm((current) => ({
            ...current,
            phone: digitsOnly,
        }));

        if (error === "Phone number must contain exactly 10 digits.") {
            setError("");
        }
    };

    return (
        <form onSubmit={submit} className="ui-form-grid">
            {error && <div className="standard-error">{error}</div>}

            <input
                required
                placeholder="Name"
                value={form.name}
                onChange={(e) =>
                    setForm({ ...form, name: e.target.value })
                }
            />

            <input
                placeholder="Job title"
                value={form.job_title}
                onChange={(e) =>
                    setForm({ ...form, job_title: e.target.value })
                }
            />

            <input
                placeholder="Email"
                type="email"
                value={form.email}
                onChange={(e) =>
                    setForm({ ...form, email: e.target.value })
                }
            />

            <input
                placeholder="10-digit phone number"
                type="tel"
                inputMode="numeric"
                maxLength={10}
                value={form.phone}
                onChange={handlePhoneChange}
            />

            <input
                placeholder="Company"
                value={form.company}
                readOnly={Boolean(companyName)}
                onChange={(e) =>
                    setForm({ ...form, company: e.target.value })
                }
            />

            <div>
                <strong>Tags</strong>
                <div
                    style={{
                        display: "flex",
                        gap: 8,
                        flexWrap: "wrap",
                        marginTop: 8,
                    }}
                >
                    {tags.map((t) => (
                        <button
                            type="button"
                            key={t}
                            className={
                                form.tags.includes(t)
                                    ? "tag-selected"
                                    : ""
                            }
                            onClick={() => toggle(t)}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <Button type="submit">Add stakeholder</Button>
        </form>
    );
}
