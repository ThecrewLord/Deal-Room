import api from "./axiosClient";

export const getAccounts = async () => {
    const response = await api.get("/accounts");
    return response.data;
};
