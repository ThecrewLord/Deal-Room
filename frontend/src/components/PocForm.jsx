import { useState } from "react";
import { createPoc } from "../api/pocApi";
import "./PocForm.css";

const REQUIRED_FIELDS = [
  "objective",
  "success_metric",
  "target_date",
  "failure_condition",
  "stakeholder_signoff",
];

export default function PocForm({ opportunityId, onSuccess }) {
  const [form, setForm] = useState({
    poc_name: "",
    objective: "",
    success_metric: "",
    target_date: "",
    failure_condition: "",
    stakeholder_signoff: false,
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  };

  const isFieldComplete = (field) => {
    const value = form[field];
    return typeof value === "boolean" ? value === true : value.trim() !== "";
  };

  const completedCount = REQUIRED_FIELDS.filter(isFieldComplete).length;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createPoc({ ...form, opportunity_id: opportunityId });
      setForm({
        poc_name: "",
        objective: "",
        success_metric: "",
        target_date: "",
        failure_condition: "",
        stakeholder_signoff: false,
      });
      onSuccess?.();
    } catch (err) {
      setError("Could not save — check that every required field below is filled in.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="poc-form-wrap">
      <div className="poc-rail">
        <div className="poc-rail-count">{completedCount}/5</div>
        <div className="poc-rail-dots">
          {REQUIRED_FIELDS.map((field) => (
            <div
              key={field}
              className={`poc-dot ${isFieldComplete(field) ? "filled" : ""}`}
              title={field.replace(/_/g, " ")}
            />
          ))}
        </div>
      </div>

      <form className="poc-card" onSubmit={handleSubmit}>
        <h3>New POC</h3>
        <p className="poc-subtitle">Exit criteria are required before this POC can be saved.</p>

        <div className="poc-field">
          <label>POC Name</label>
          <input
            type="text"
            name="poc_name"
            value={form.poc_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="poc-field">
          <label>Objective</label>
          <textarea
            name="objective"
            value={form.objective}
            onChange={handleChange}
            placeholder="What is being tested?"
            required
          />
          <span className="hint">e.g. System sustains target throughput for 72 continuous hours</span>
        </div>

        <div className="poc-field">
          <label>Success Metric</label>
          <input
            type="text"
            name="success_metric"
            value={form.success_metric}
            onChange={handleChange}
            placeholder="Must be measurable"
            required
          />
          <span className="hint">e.g. Throughput ≥ 1200 units/hr sustained</span>
        </div>

        <div className="poc-field">
          <label>Target Date</label>
          <input
            type="date"
            name="target_date"
            value={form.target_date}
            onChange={handleChange}
            required
          />
        </div>

        <div className="poc-field">
          <label>Failure / Fallback Condition</label>
          <textarea
            name="failure_condition"
            value={form.failure_condition}
            onChange={handleChange}
            placeholder="What happens if the metric isn't met?"
            required
          />
          <span className="hint">e.g. Deal moves to Closed Lost</span>
        </div>

        <div className="poc-checkbox-row">
          <input
            type="checkbox"
            id="stakeholder_signoff"
            name="stakeholder_signoff"
            checked={form.stakeholder_signoff}
            onChange={handleChange}
          />
          <label htmlFor="stakeholder_signoff">Stakeholder sign-off confirmed</label>
        </div>

        {error && <div className="poc-error">{error}</div>}

        <button type="submit" className="poc-submit" disabled={submitting}>
          {submitting ? "Saving…" : "Save POC"}
        </button>
      </form>
    </div>
  );
}
