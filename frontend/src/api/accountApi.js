import api from "./axiosClient";
export const getAccounts = async () => (await api.get("/accounts")).data;
export const createAccount = async (payload) => (await api.post("/accounts", payload)).data;
export const archiveAccount = async (id) => (await api.post(`/accounts/${id}/archive`)).data;
export const banAccount = async (id) => (await api.post(`/accounts/${id}/ban`)).data;

export const unbanAccount = async (id) => (await api.post(`/accounts/${id}/unban`)).data;

export const restoreAccount = async (id) => (await api.post(`/accounts/${id}/restore`)).data;
