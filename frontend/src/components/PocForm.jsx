import { useEffect, useMemo, useState } from "react";
import { getOpportunities } from "../api/opportunityApi";
import "./PocForm.css";

const REQUIRED_FIELDS = [
    "poc_name",
    "objective",
    "success_metric",
    "exit_criteria",
    "target_date",
    "failure_condition",
];

const INITIAL_FORM = {
    opportunity_id: "",
    poc_name: "",
    objective: "",
    success_metric: "",
    exit_criteria: "",
    target_date: "",
    failure_condition: "",
    remarks: "",
    stakeholder_signoff: false,
};

export default function PocForm({
    onSubmit,
    submitting = false,
    onCancel,
}) {
    const [form, setForm] = useState(INITIAL_FORM);
    const [opportunities, setOpportunities] = useState([]);
    const [loadingOpportunities, setLoadingOpportunities] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const loadOpportunities = async () => {
            try {
                setLoadingOpportunities(true);
                const data = await getOpportunities();
                setOpportunities(data || []);
            } catch (err) {
                setError(
                    err?.response?.data?.message ||
                    "Unable to load opportunities."
                );
            } finally {
                setLoadingOpportunities(false);
            }
        };

        loadOpportunities();
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;

        setForm((current) => ({
            ...current,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const isFieldComplete = (field) => {
        const value = form[field];

        if (typeof value === "boolean") {
            return value;
        }

        return String(value || "").trim() !== "";
    };

    const completedCount = useMemo(
        () => REQUIRED_FIELDS.filter(isFieldComplete).length,
        [form]
    );

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

        if (!form.opportunity_id) {
            setError("Please select an opportunity.");
            return;
        }

        try {
            await onSubmit({
                ...form,
                opportunity_id: Number(form.opportunity_id),
            });

            setForm(INITIAL_FORM);
        } catch (err) {
            setError(
                err?.response?.data?.message ||
                "Could not save the POC. Please check the required fields."
            );
        }
    };

    return (
        <div className="poc-form-wrap">
            <div className="poc-rail">
                <div className="poc-rail-count">
                    {completedCount}/{REQUIRED_FIELDS.length}
                </div>

                <div className="poc-rail-dots">
                    {REQUIRED_FIELDS.map((field) => (
                        <div
                            key={field}
                            className={`poc-dot ${
                                isFieldComplete(field) ? "filled" : ""
                            }`}
                            title={field.replace(/_/g, " ")}
                        />
                    ))}
                </div>
            </div>

            <form className="poc-card" onSubmit={handleSubmit}>
                <h3>Create New POC</h3>

                <p className="poc-subtitle">
                    Complete the POC definition and exit criteria before saving.
                </p>

                <div className="poc-field">
                    <label htmlFor="opportunity_id">
                        Opportunity
                    </label>

                    <select
                        id="opportunity_id"
                        name="opportunity_id"
                        value={form.opportunity_id}
                        onChange={handleChange}
                        required
                        disabled={loadingOpportunities || submitting}
                    >
                        <option value="">
                            {loadingOpportunities
                                ? "Loading opportunities…"
                                : "Select an opportunity"}
                        </option>

                        {opportunities.map((opportunity) => (
                            <option
                                key={opportunity.opportunity_id}
                                value={opportunity.opportunity_id}
                            >
                                {opportunity.opportunity_name}
                                {opportunity.account_name
                                    ? ` — ${opportunity.account_name}`
                                    : ""}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="poc-field">
                    <label htmlFor="poc_name">
                        POC Name
                    </label>

                    <input
                        id="poc_name"
                        type="text"
                        name="poc_name"
                        value={form.poc_name}
                        onChange={handleChange}
                        placeholder="e.g. Network Performance POC"
                        required
                        disabled={submitting}
                    />
                </div>

                <div className="poc-field">
                    <label htmlFor="objective">
                        Objective
                    </label>

                    <textarea
                        id="objective"
                        name="objective"
                        value={form.objective}
                        onChange={handleChange}
                        placeholder="What is being tested?"
                        required
                        disabled={submitting}
                    />

                    <span className="hint">
                        e.g. System sustains target throughput for 72 continuous hours
                    </span>
                </div>

                <div className="poc-field">
                    <label htmlFor="success_metric">
                        Success Metric
                    </label>

                    <input
                        id="success_metric"
                        type="text"
                        name="success_metric"
                        value={form.success_metric}
                        onChange={handleChange}
                        placeholder="Must be measurable"
                        required
                        disabled={submitting}
                    />

                    <span className="hint">
                        e.g. Throughput ≥ 1200 units/hr sustained
                    </span>
                </div>

                <div className="poc-field">
                    <label htmlFor="exit_criteria">
                        Exit Criteria
                    </label>

                    <textarea
                        id="exit_criteria"
                        name="exit_criteria"
                        value={form.exit_criteria}
                        onChange={handleChange}
                        placeholder="What must be true for the POC to be considered successful?"
                        required
                        disabled={submitting}
                    />

                    <span className="hint">
                        Define the measurable conditions required to close the POC.
                    </span>
                </div>

                <div className="poc-field">
                    <label htmlFor="target_date">
                        Target Date
                    </label>

                    <input
                        id="target_date"
                        type="date"
                        name="target_date"
                        value={form.target_date}
                        onChange={handleChange}
                        required
                        disabled={submitting}
                    />
                </div>

                <div className="poc-field">
                    <label htmlFor="failure_condition">
                        Failure / Fallback Condition
                    </label>

                    <textarea
                        id="failure_condition"
                        name="failure_condition"
                        value={form.failure_condition}
                        onChange={handleChange}
                        placeholder="What happens if the success metric isn't met?"
                        required
                        disabled={submitting}
                    />

                    <span className="hint">
                        e.g. Deal moves to Closed Lost
                    </span>
                </div>

                <div className="poc-field">
                    <label htmlFor="remarks">
                        Remarks <span className="optional-tag">Optional</span>
                    </label>

                    <textarea
                        id="remarks"
                        name="remarks"
                        value={form.remarks}
                        onChange={handleChange}
                        placeholder="Add any additional context..."
                        disabled={submitting}
                    />
                </div>

                <div className="poc-checkbox-row">
                    <input
                        type="checkbox"
                        id="stakeholder_signoff"
                        name="stakeholder_signoff"
                        checked={form.stakeholder_signoff}
                        onChange={handleChange}
                        disabled={submitting}
                    />

                    <label htmlFor="stakeholder_signoff">
                        Stakeholder sign-off confirmed
                    </label>
                </div>

                {error && (
                    <div className="poc-error">
                        {error}
                    </div>
                )}

                <div className="poc-form-actions">
                    {onCancel && (
                        <button
                            type="button"
                            className="poc-cancel"
                            onClick={onCancel}
                            disabled={submitting}
                        >
                            Cancel
                        </button>
                    )}

                    <button
                        type="submit"
                        className="poc-submit"
                        disabled={
                            submitting ||
                            loadingOpportunities
                        }
                    >
                        {submitting ? "Creating POC…" : "Create POC"}
                    </button>
                </div>
            </form>
        </div>
    );
}