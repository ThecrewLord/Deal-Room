import api from "./axiosClient";

export const getSolutionDesign = async (opportunityId) =>
    (await api.get(`/opportunities/${opportunityId}/solution-design`)).data;

export const updateSolutionDesign = async (opportunityId, payload) =>
    (await api.patch(`/opportunities/${opportunityId}/solution-design`, payload)).data;
