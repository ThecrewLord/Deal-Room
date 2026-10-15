import api from "./axiosClient";

export const getNotifications = async (unreadOnly = false) => {
    const response = await api.get("/notifications", {
        params: { unread_only: unreadOnly },
    });
    return response.data;
};

export const markNotificationRead = async (notificationId) => {
    const response = await api.post(`/notifications/${notificationId}/read`);
    return response.data;
};

export const markAllNotificationsRead = async () => {
    const response = await api.post("/notifications/read-all");
    return response.data;
};
