import api from "./axiosClient";

export const getPendingPreSalesAssignments = async () => {
    const response = await api.get("/opportunities/pre-sales-assignment-queue");
    return response.data;
};

export const getEligibleSolutionEngineers = async () => {
    const response = await api.get(
        "/opportunities/pre-sales-assignment-candidates/Solution%20Engineer"
    );
    return response.data;
};


export const finalizePreSalesAssignment = async (opportunityId, payload) => {
    const response = await api.post(
        `/opportunities/${opportunityId}/finalize-pre-sales-assignment`,
        payload
    );
    return response.data;
};

export const getTechnicalTeam = async (opportunityId) => {
    const response = await api.get(
        `/opportunities/${opportunityId}/technical-team`
    );
    return response.data;
};