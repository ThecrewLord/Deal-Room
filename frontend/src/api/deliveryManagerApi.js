import api from "./axiosClient";

export const getPocAssignmentQueue = async (params = {}) => (await api.get("/v2/delivery-manager/poc-assignments", { params })).data;
export const getDeliveryAssignmentQueue = async (params = {}) => (await api.get("/v2/delivery-manager/delivery-assignments", { params })).data;
export const getPocTeamCandidates = async () => (await api.get("/v2/poc-team-candidates")).data;
export const assignPocTeam = async (pocId, memberIds, expectedVersion) => (await api.post(`/v2/pocs/${pocId}/team`, { member_ids: memberIds, expected_version: expectedVersion })).data;
export const reassignPocTeam = async (opportunityId, memberIds, expectedVersion) => (await api.put(`/v2/opportunity/${opportunityId}/poc-team`, { member_ids: memberIds, expected_version: expectedVersion })).data;
export const getDeliveryTeamCandidates = async () => (await api.get("/v2/delivery-team-candidates")).data;
export const assignDeliveryTeam = async (projectId, memberIds, expectedVersion) => (await api.put(`/v2/delivery-project/${projectId}/members`, { member_ids: memberIds, expected_version: expectedVersion })).data;
export const getDeliveryTeamPerformance = async () => (await api.get("/delivery-manager/team-performance")).data;
export const getDeliveryEmployeePerformance = async (employeeId) => (await api.get(`/delivery-manager/team-performance/${employeeId}`)).data;
