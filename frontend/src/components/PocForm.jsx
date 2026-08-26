import { useEffect, useMemo, useRef, useState } from "react";
import { Search, ChevronDown, Check, X } from "lucide-react";
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

export default function PocForm({ onSubmit, submitting = false, onCancel }) {
    const [form, setForm] = useState(INITIAL_FORM);
    const [opportunities, setOpportunities] = useState([]);
    const [loadingOpportunities, setLoadingOpportunities] = useState(true);
    const [error, setError] = useState("");
    const [opportunitySearch, setOpportunitySearch] = useState("");
    const [showOpportunityOptions, setShowOpportunityOptions] = useState(false);
    const opportunityPickerRef = useRef(null);

    useEffect(() => {
        const loadOpportunities = async () => {
            try {
                setLoadingOpportunities(true);
                const data = await getOpportunities();
                setOpportunities(Array.isArray(data) ? data : []);
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

    useEffect(() => {
        const handlePointerDown = (event) => {
            if (!opportunityPickerRef.current?.contains(event.target)) {
                setShowOpportunityOptions(false);
            }
        };

        document.addEventListener("mousedown", handlePointerDown);
        return () => document.removeEventListener("mousedown", handlePointerDown);
    }, []);

    const selectedOpportunity = useMemo(
        () => opportunities.find(
            (opportunity) => String(opportunity.opportunity_id) === String(form.opportunity_id)
        ),
        [opportunities, form.opportunity_id]
    );

    const filteredOpportunities = useMemo(() => {
        const query = opportunitySearch.trim().toLowerCase();
        if (!query) return opportunities.slice(0, 25);

        return opportunities
            .filter((opportunity) => {
                const haystack = [
                    opportunity.opportunity_name,
                    opportunity.account_name,
                    opportunity.sales_owner?.full_name,
                    opportunity.current_stage?.stage_name,
                ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();

                return haystack.includes(query);
            })
            .slice(0, 25);
    }, [opportunities, opportunitySearch]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;

        setForm((current) => ({
            ...current,
            [name]: type === "checkbox" ? checked : value,
        }));
    };

    const selectOpportunity = (opportunity) => {
        setForm((current) => ({
            ...current,
            opportunity_id: String(opportunity.opportunity_id),
        }));
        setOpportunitySearch("");
        setShowOpportunityOptions(false);
    };

    const clearOpportunity = () => {
        setForm((current) => ({ ...current, opportunity_id: "" }));
        setOpportunitySearch("");
        setShowOpportunityOptions(true);
    };

    const isFieldComplete = (field) => {
        const value = form[field];
        if (typeof value === "boolean") return value;
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
            setError("Please select an existing opportunity.");
            return;
        }

        try {
            await onSubmit({
                ...form,
                opportunity_id: Number(form.opportunity_id),
            });
            setForm(INITIAL_FORM);
            setOpportunitySearch("");
        } catch (err) {
            setError(
                err?.response?.data?.message ||
                "Could not save the POC. Please check the required fields."
            );
        }
    };

    return (
        <div className="poc-form-wrap">
            <form className="poc-card" onSubmit={handleSubmit}>
                <div className="poc-form-heading">
                    <div>
                        <span className="poc-eyebrow">TECHNICAL WORK</span>
                        <h3>Create New POC</h3>
                        <p className="poc-subtitle">
                            Define the technical proof of concept and its success criteria.
                        </p>
                    </div>

                    <div className="poc-progress" aria-label={`${completedCount} of ${REQUIRED_FIELDS.length} required fields completed`}>
                        <strong>{completedCount}/{REQUIRED_FIELDS.length}</strong>
                        <span>Required complete</span>
                    </div>
                </div>

                <div className="poc-form-grid">
                    <div className="poc-field poc-field-full">
                        <label htmlFor="opportunity_search">Opportunity</label>
                        <div className="poc-opportunity-picker" ref={opportunityPickerRef}>
                            {selectedOpportunity ? (
                                <div className="poc-selected-opportunity">
                                    <div className="poc-selected-main">
                                        <strong>{selectedOpportunity.opportunity_name}</strong>
                                        <span>
                                            {selectedOpportunity.account_name || "Account not specified"}
                                            {selectedOpportunity.current_stage?.stage_name
                                                ? ` · ${selectedOpportunity.current_stage.stage_name}`
                                                : ""}
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        className="poc-clear-selection"
                                        onClick={clearOpportunity}
                                        disabled={submitting}
                                        aria-label="Change opportunity"
                                    >
                                        <X size={15} />
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <div className="poc-search-control">
                                        <Search size={16} />
                                        <input
                                            id="opportunity_search"
                                            type="text"
                                            value={opportunitySearch}
                                            onChange={(e) => {
                                                setOpportunitySearch(e.target.value);
                                                setShowOpportunityOptions(true);
                                            }}
                                            onFocus={() => setShowOpportunityOptions(true)}
                                            placeholder={loadingOpportunities ? "Loading opportunities…" : "Search opportunity or account…"}
                                            disabled={loadingOpportunities || submitting}
                                            autoComplete="off"
                                        />
                                        <ChevronDown size={16} className={showOpportunityOptions ? "is-open" : ""} />
                                    </div>

                                    {showOpportunityOptions && !loadingOpportunities && (
                                        <div className="poc-opportunity-menu">
                                            {filteredOpportunities.length ? (
                                                filteredOpportunities.map((opportunity) => (
                                                    <button
                                                        type="button"
                                                        className="poc-opportunity-option"
                                                        key={opportunity.opportunity_id}
                                                        onClick={() => selectOpportunity(opportunity)}
                                                    >
                                                        <span className="poc-option-check"><Check size={13} /></span>
                                                        <span className="poc-option-main">
                                                            <strong>{opportunity.opportunity_name}</strong>
                                                            <span>
                                                                {opportunity.account_name || "Account not specified"}
                                                                {opportunity.current_stage?.stage_name
                                                                    ? ` · ${opportunity.current_stage.stage_name}`
                                                                    : ""}
                                                            </span>
                                                        </span>
                                                    </button>
                                                ))
                                            ) : (
                                                <div className="poc-opportunity-empty">
                                                    No existing opportunities match your search.
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                        <span className="hint">Only existing opportunities can be linked to a POC.</span>
                    </div>

                    <div className="poc-field">
                        <label htmlFor="poc_name">POC Name</label>
                        <input id="poc_name" type="text" name="poc_name" value={form.poc_name} onChange={handleChange} placeholder="e.g. Network Performance POC" required disabled={submitting} />
                    </div>

                    <div className="poc-field">
                        <label htmlFor="target_date">Target Date</label>
                        <input id="target_date" type="date" name="target_date" value={form.target_date} onChange={handleChange} required disabled={submitting} />
                    </div>

                    <div className="poc-field poc-field-full">
                        <label htmlFor="objective">Objective</label>
                        <textarea id="objective" name="objective" value={form.objective} onChange={handleChange} placeholder="What is being tested?" required disabled={submitting} />
                        <span className="hint">e.g. System sustains target throughput for 72 continuous hours</span>
                    </div>

                    <div className="poc-field poc-field-full">
                        <label htmlFor="success_metric">Success Metric</label>
                        <input id="success_metric" type="text" name="success_metric" value={form.success_metric} onChange={handleChange} placeholder="Must be measurable" required disabled={submitting} />
                        <span className="hint">e.g. Throughput ≥ 1200 units/hr sustained</span>
                    </div>

                    <div className="poc-field poc-field-full">
                        <label htmlFor="exit_criteria">Exit Criteria</label>
                        <textarea id="exit_criteria" name="exit_criteria" value={form.exit_criteria} onChange={handleChange} placeholder="What must be true for the POC to be considered successful?" required disabled={submitting} />
                        <span className="hint">Define the measurable conditions required to close the POC.</span>
                    </div>

                    <div className="poc-field poc-field-full">
                        <label htmlFor="failure_condition">Failure / Fallback Condition</label>
                        <textarea id="failure_condition" name="failure_condition" value={form.failure_condition} onChange={handleChange} placeholder="What happens if the success metric isn't met?" required disabled={submitting} />
                        <span className="hint">e.g. Deal moves to Closed Lost</span>
                    </div>

                    <div className="poc-field poc-field-full">
                        <label htmlFor="remarks">Remarks <span className="optional-tag">Optional</span></label>
                        <textarea id="remarks" name="remarks" value={form.remarks} onChange={handleChange} placeholder="Add any additional context..." disabled={submitting} />
                    </div>
                </div>

                <label className="poc-checkbox-row">
                    <input type="checkbox" id="stakeholder_signoff" name="stakeholder_signoff" checked={form.stakeholder_signoff} onChange={handleChange} disabled={submitting} />
                    <span>Stakeholder sign-off confirmed</span>
                </label>

                {error && <div className="poc-error" role="alert">{error}</div>}

                <div className="poc-form-actions">
                    {onCancel && (
                        <button type="button" className="poc-cancel" onClick={onCancel} disabled={submitting}>Cancel</button>
                    )}
                    <button type="submit" className="poc-submit" disabled={submitting || loadingOpportunities || !form.opportunity_id}>
                        {submitting ? "Creating POC…" : "Create POC"}
                    </button>
                </div>
            </form>
        </div>
    );
}
