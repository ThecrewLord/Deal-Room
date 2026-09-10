import api from "./axiosClient";
export const getAccounts = async () => (await api.get("/accounts")).data;
export const createAccount = async (payload) => (await api.post("/accounts", payload)).data;
export const archiveAccount = async (id) => (await api.post(`/accounts/${id}/archive`)).data;
export const banAccount = async (id) => (await api.post(`/accounts/${id}/ban`)).data;
