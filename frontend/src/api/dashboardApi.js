import axiosClient from "./axiosClient";

const localCalendarDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
};

export const getDashboardSummary = async () => {
    const response = await axiosClient.get("/dashboard", { params: { today: localCalendarDate() } });
    return response.data;
};

export const getDashboardFollowUps = async ({ filter = "all", page = 1, pageSize = 10 } = {}) => {
    const response = await axiosClient.get("/dashboard/follow-ups", {
        params: { filter, page, page_size: pageSize, today: localCalendarDate() },
    });
    return response.data;
};
