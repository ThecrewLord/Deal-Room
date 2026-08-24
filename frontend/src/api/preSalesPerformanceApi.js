import axiosClient from "./axiosClient";

export const getPreSalesTeamPerformance = async () => {
    const response = await axiosClient.get("/pre-sales-manager/team-performance");
    return response.data;
};

export const getPreSalesEmployeePerformance = async (employeeId) => {
    const response = await axiosClient.get(`/pre-sales-manager/team-performance/${employeeId}`);
    return response.data;
};
