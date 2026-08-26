import api from "./axiosClient";

export const searchAuthorized = async (query, type) => {
    const response = await api.get("/search", {
        params: { q: query, ...(type ? { type } : {}) },
    });
    return response.data;
};
