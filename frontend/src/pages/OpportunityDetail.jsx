import { useState, useEffect } from "react";
import PocForm from "../components/PocForm";
import StakeholderForm from "../components/StakeholderForm";
import { getPocsByOpportunity } from "../api/pocApi";

export default function OpportunityDetail() {
  const opportunityId = 1;
  const [pocs, setPocs] = useState([]);

  const loadPocs = async () => {
    const data = await getPocsByOpportunity(opportunityId);
    setPocs(data);
  };

  useEffect(() => {
    loadPocs();
  }, []);

  return (
    <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "40px" }}>
      <h2>Opportunity #{opportunityId}</h2>

      <div>
        <PocForm opportunityId={opportunityId} onSuccess={loadPocs} />

        <h3 style={{ marginTop: "32px" }}>Existing POCs</h3>
        {pocs.length === 0 && <p>No POCs yet.</p>}
        <ul>
          {pocs.map((poc) => (
            <li key={poc.poc_id}>
              <strong>{poc.poc_name}</strong> — {poc.objective} (Target: {poc.target_date})
            </li>
          ))}
        </ul>
      </div>

      <StakeholderForm opportunityId={opportunityId} />
    </div>
  );
}
