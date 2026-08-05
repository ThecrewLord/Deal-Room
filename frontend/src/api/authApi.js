import axiosClient from "./axiosClient";

export const login = (payload) =>
    axiosClient.post("/auth/login", payload);

export const signup = (payload) =>
    axiosClient.post("/auth/signup", payload);

export const logout = () =>
    axiosClient.post("/auth/logout");

export const getCurrentUser = () =>
    axiosClient.get("/auth/me");