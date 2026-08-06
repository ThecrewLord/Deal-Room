const BASE_URL = "/api/stakeholder";

export async function createStakeholder(stakeholderData) {
  const res = await fetch(BASE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(stakeholderData),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(JSON.stringify(err));
  }
  return res.json();
}

export async function getStakeholdersByOpportunity(opportunityId) {
  const res = await fetch(`${BASE_URL}/opportunity/${opportunityId}`);
  if (!res.ok) throw new Error("Failed to fetch stakeholders");
  return res.json();
}

export async function updateStakeholder(stakeholderId, data) {
  const res = await fetch(`${BASE_URL}/${stakeholderId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(JSON.stringify(err));
  }
  return res.json();
}

export async function deleteStakeholder(stakeholderId) {
  const res = await fetch(`${BASE_URL}/${stakeholderId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete stakeholder");
  return res.json();
}
