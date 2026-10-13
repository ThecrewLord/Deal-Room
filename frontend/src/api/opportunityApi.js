import api from "./axiosClient";

export const getOpportunities = async () => (await api.get("/opportunities")).data;
export const createOpportunity = async (payload) => (await api.post("/opportunities", payload)).data;
export const getOpportunity = async (id) => (await api.get(`/opportunities/${id}`)).data;
export const getOpportunityStageHistory = async (id) => (await api.get(`/opportunities/${id}/stage-history`)).data;
export const getOpportunityValueHistory = async (id) => (await api.get(`/opportunities/${id}/value-history`)).data;
export const changeOpportunityValue = async (id, payload) => (await api.post(`/opportunities/${id}/value`, payload)).data;
export const getRevenueReport = async () => (await api.get("/opportunities/revenue")).data;
export const updateOpportunity = async (id, payload) => (await api.put(`/opportunities/${id}`, payload)).data;
export const submitOpportunityForReview = async (id, expected_version) =>
    (await api.post(`/opportunities/${id}/submit-lead`, { expected_version })).data;
export const getSalesManagerReviewQueue = async () => (await api.get("/opportunities/review-queue")).data;
export const getEligibleSalesOwners = async () => (await api.get("/opportunities/sales-owners")).data;
export const reviewOpportunity = async (id, payload) => (await api.post(`/opportunities/${id}/review`, payload)).data;
export const advanceToRfx = async (id, expected_version) =>
    (await api.post(`/opportunities/${id}/advance-to-rfx`, { expected_version })).data;
export const advanceToPoc = async (id, expected_version) =>
    (await api.post(`/opportunities/${id}/advance-to-poc`, { expected_version })).data;
export const advanceToNegotiations = async (id, expected_version) =>
    (await api.post(`/opportunities/${id}/advance-to-negotiations`, { expected_version })).data;
export const requestClosedWon = async (id, payload) => (await api.post(`/opportunities/${id}/request-closed-won`, payload)).data;
export const approveClosedWon = async (id, payload) => (await api.post(`/opportunities/${id}/approve-closed-won`, payload)).data;
export const rejectClosedWon = async (id, payload) => (await api.post(`/opportunities/${id}/reject-closed-won`, payload)).data;
export const closeWon = async (id, payload) => (await api.post(`/opportunities/${id}/close-won`, payload)).data;
export const closeLost = async (id, payload) => (await api.post(`/opportunities/${id}/close-lost`, payload)).data;
export const markStalled = async (id, expected_version) =>
    (await api.post(`/opportunities/${id}/mark-stalled`, { expected_version })).data;
export const markActive = async (id, expected_version) =>
    (await api.post(`/opportunities/${id}/mark-active`, { expected_version })).data;
