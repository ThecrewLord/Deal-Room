import api from "./axiosClient";
export async function createStakeholder(data){return (await api.post("/stakeholder",data)).data}
export async function getStakeholdersByOpportunity(id){return (await api.get(`/stakeholder/opportunity/${id}`)).data}
export async function getStakeholders(){return (await api.get("/stakeholder")).data}
export async function updateStakeholder(id,data){return (await api.put(`/stakeholder/${id}`,data)).data}
export async function deleteStakeholder(id){return (await api.delete(`/stakeholder/${id}`)).data}
