import axios from "axios";

import api from "../api/axiosClient";

import {
    getRefreshToken,
} from "./authStorage";

const BASE_URL =
    import.meta.env.VITE_API_URL;

const authApi = {
    login(payload) {
        return api
            .post("/auth/login", payload)
            .then((res) => res.data);
    },

    signup(payload) {
        return api
            .post("/auth/signup", payload)
            .then((res) => res.data);
    },

    logout() {
        return api
            .post("/auth/logout")
            .then((res) => res.data);
    },

    refresh() {
        return axios
            .post(
                `${BASE_URL}/auth/refresh`,
                {},
                {
                    headers: {
                        Authorization: `Bearer ${getRefreshToken()}`,
                    },
                }
            )
            .then((res) => res.data);
    },

    selectRole(role) {
        return api
            .post("/auth/select-role", {
                role,
            })
            .then((res) => res.data);
    },

    me() {
        return api
            .get("/auth/me")
            .then((res) => res.data);
    },
};

export default authApi;