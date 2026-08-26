import { useState } from "react";
import { createStakeholder } from "../api/stakeholderApi";
import "./StakeholderForm.css";

const INFLUENCE_LEVELS = ["Decision Maker", "Influencer", "User", "Blocker"];

export default function StakeholderForm({ opportunityId, onCreated }) {
  const [form, setForm] = useState({
    stakeholder_name: "",
    designation: "",
    email: "",
    phone: "",
    influence_level: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createStakeholder({ ...form, opportunity_id: opportunityId });
      setForm({
        stakeholder_name: "",
        designation: "",
        email: "",
        phone: "",
        influence_level: "",
      });
      onCreated?.();
    } catch (err) {
      setError(
        err?.response?.data?.message ||
        "Could not save stakeholder — check the fields and try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stakeholder-card stakeholder-form-only">
      <div className="stakeholder-form-heading">
        <div>
          <span className="stakeholder-eyebrow">CUSTOMER CONTACT</span>
          <h3>Add Stakeholder</h3>
          <p className="stakeholder-subtitle">
            Add a customer-side contact to this opportunity.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="stakeholder-form-grid">
          <div className="stakeholder-field">
            <label htmlFor="stakeholder_name">Name</label>
            <input id="stakeholder_name" type="text" name="stakeholder_name" value={form.stakeholder_name} onChange={handleChange} required />
          </div>

          <div className="stakeholder-field">
            <label htmlFor="designation">Designation</label>
            <input id="designation" type="text" name="designation" value={form.designation} onChange={handleChange} placeholder="e.g. VP Engineering" />
          </div>

          <div className="stakeholder-field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" name="email" value={form.email} onChange={handleChange} />
          </div>

          <div className="stakeholder-field">
            <label htmlFor="phone">Phone</label>
            <input id="phone" type="text" name="phone" value={form.phone} onChange={handleChange} />
          </div>

          <div className="stakeholder-field stakeholder-field-full">
            <label htmlFor="influence_level">Influence Level</label>
            <select id="influence_level" name="influence_level" value={form.influence_level} onChange={handleChange}>
              <option value="">Select...</option>
              {INFLUENCE_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
            </select>
          </div>
        </div>

        {error && <div className="stakeholder-error" role="alert">{error}</div>}

        <div className="stakeholder-form-actions">
          <button type="submit" className="stakeholder-submit" disabled={submitting}>
            {submitting ? "Saving…" : "Add Stakeholder"}
          </button>
        </div>
      </form>
    </div>
  );
}
