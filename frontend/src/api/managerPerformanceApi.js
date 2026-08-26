import api from "./axiosClient";

export const getTeamPerformance = async () =>
    (await api.get("/sales-manager/team-performance")).data;

export const getEmployeePerformance = async (employeeId) =>
    (await api.get(`/sales-manager/team-performance/${employeeId}`)).data;
