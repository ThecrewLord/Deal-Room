import api from "./axiosClient";

export async function createStakeholder(stakeholderData) {
  const res = await api.post("/stakeholder", stakeholderData);
  return res.data;
}

export async function getStakeholdersByOpportunity(opportunityId) {
  const res = await api.get(`/stakeholder/opportunity/${opportunityId}`);
  return res.data;
}

export async function updateStakeholder(stakeholderId, data) {
  const res = await api.put(`/stakeholder/${stakeholderId}`, data);
  return res.data;
}

export async function deleteStakeholder(stakeholderId) {
  const res = await api.delete(`/stakeholder/${stakeholderId}`);
  return res.data;
}
