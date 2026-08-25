import api from "./axiosClient";

export const getAccounts = async () => {
    const response = await api.get("/accounts");
    return response.data;
};

export const createAccount = async (payload) => {
    const response = await api.post("/accounts", payload);
    return response.data;
};
