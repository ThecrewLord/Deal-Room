import axiosClient from "./axiosClient";

export const getDashboardSummary = async () => {
    const response = await axiosClient.get("/dashboard");
    return response.data;
};