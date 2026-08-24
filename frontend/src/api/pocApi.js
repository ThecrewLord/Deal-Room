import api from "./axiosClient";

export const requestPoc = async (payload) => (await api.post("/poc/request", payload)).data;
export const getPoc = async (id) => (await api.get(`/poc/${id}`)).data;
export const getPocsByOpportunity = async (opportunityId) =>
    (await api.get(`/poc/opportunity/${opportunityId}`)).data;
export const getPendingPocApprovals = async () =>
    (await api.get("/poc/pending-approvals")).data;
export const updatePocDesign = async (id, payload) =>
    (await api.patch(`/poc/${id}/design`, payload)).data;
export const approvePoc = async (id, payload) =>
    (await api.post(`/poc/${id}/approve`, payload)).data;
export const rejectPoc = async (id, payload) =>
    (await api.post(`/poc/${id}/reject`, payload)).data;
export const startPocExecution = async (id, payload) =>
    (await api.post(`/poc/${id}/start-execution`, payload)).data;
export const submitPocResult = async (id, payload) =>
    (await api.post(`/poc/${id}/submit-result`, payload)).data;
export const completePoc = async (id, payload) =>
    (await api.post(`/poc/${id}/complete`, payload)).data;
export const deletePoc = async () => {
    throw new Error("POC deletion is disabled.");
};
