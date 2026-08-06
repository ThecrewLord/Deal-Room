import { useState, useEffect } from "react";
import {
  createStakeholder,
  getStakeholdersByOpportunity,
} from "../api/stakeholderApi";
import "./StakeholderForm.css";

const INFLUENCE_LEVELS = ["Decision Maker", "Influencer", "User", "Blocker"];

function badgeClass(level) {
  return level.toLowerCase().replace(" ", "-");
}

export default function StakeholderForm({ opportunityId }) {
  const [form, setForm] = useState({
    stakeholder_name: "",
    designation: "",
    email: "",
    phone: "",
    influence_level: "",
  });
  const [stakeholders, setStakeholders] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadStakeholders = async () => {
    try {
      const data = await getStakeholdersByOpportunity(opportunityId);
      setStakeholders(data);
    } catch (err) {
      // silently ignore for now
    }
  };

  useEffect(() => {
    loadStakeholders();
  }, []);

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
      loadStakeholders();
    } catch (err) {
      setError("Could not save stakeholder — check the fields and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stakeholder-card">
      <h3>Stakeholders</h3>
      <p className="stakeholder-subtitle">Who's involved on the customer's side for this deal.</p>

      <form onSubmit={handleSubmit}>
        <div className="stakeholder-field">
          <label>Name</label>
          <input
            type="text"
            name="stakeholder_name"
            value={form.stakeholder_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="stakeholder-field">
          <label>Designation</label>
          <input
            type="text"
            name="designation"
            value={form.designation}
            onChange={handleChange}
            placeholder="e.g. VP Engineering"
          />
        </div>

        <div className="stakeholder-field">
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
          />
        </div>

        <div className="stakeholder-field">
          <label>Phone</label>
          <input
            type="text"
            name="phone"
            value={form.phone}
            onChange={handleChange}
          />
        </div>

        <div className="stakeholder-field">
          <label>Influence Level</label>
          <select
            name="influence_level"
            value={form.influence_level}
            onChange={handleChange}
          >
            <option value="">Select...</option>
            {INFLUENCE_LEVELS.map((level) => (
              <option key={level} value={level}>{level}</option>
            ))}
          </select>
        </div>

        {error && <div className="stakeholder-error">{error}</div>}

        <button type="submit" className="stakeholder-submit" disabled={submitting}>
          {submitting ? "Saving…" : "Add Stakeholder"}
        </button>
      </form>

      <ul className="stakeholder-list">
        {stakeholders.map((s) => (
          <li key={s.stakeholder_id} className="stakeholder-list-item">
            <span className="name">{s.stakeholder_name}</span>
            {s.influence_level && (
              <span className={`influence-badge ${badgeClass(s.influence_level)}`}>
                {s.influence_level}
              </span>
            )}
            <div className="meta">
              {s.designation || "—"} {s.email ? `· ${s.email}` : ""}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
