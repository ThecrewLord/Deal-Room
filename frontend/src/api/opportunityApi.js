import api from "./axiosClient";

export const getOpportunities = async () => (await api.get("/opportunities")).data;
export const createOpportunity = async (payload) => (await api.post("/opportunities", payload)).data;
export const getOpportunity = async (id) => (await api.get(`/opportunities/${id}`)).data;
export const getOpportunityStageHistory = async (id) => (await api.get(`/opportunities/${id}/stage-history`)).data;
export const updateOpportunity = async (id, payload) => (await api.put(`/opportunities/${id}`, payload)).data;
export const qualifyOpportunity = async (id) => (await api.post(`/opportunities/${id}/qualify`)).data;
export const submitOpportunityForReview = async (id) => (await api.post(`/opportunities/${id}/submit-for-review`)).data;
export const getSalesManagerReviewQueue = async () => (await api.get("/opportunities/review-queue")).data;
export const getEligibleSalesOwners = async () => (await api.get("/opportunities/sales-owners")).data;
export const reviewOpportunity = async (id, payload) => (await api.post(`/opportunities/${id}/review`, payload)).data;
export const transitionTechnicalStage = async (id, payload) =>
    (await api.post(`/opportunities/${id}/transition-technical-stage`, payload)).data;
export const closeWon = async (id, payload) => (await api.post(`/opportunities/${id}/close-won`, payload)).data;
export const closeLost = async (id, payload) => (await api.post(`/opportunities/${id}/close-lost`, payload)).data;
