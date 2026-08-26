import axios from "axios";
import API_BASE_URL from "../config/api";

import api from "../api/axiosClient";

import {
    getRefreshToken,
} from "./authStorage";

const BASE_URL = API_BASE_URL;

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
            .post("/auth/logout", { refresh_token: getRefreshToken() })
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
        // Role selection happens before an access token exists for a
        // multi-role login, so authenticate this request explicitly with
        // the refresh token returned by /auth/login.
        return axios
            .post(
                `${BASE_URL}/auth/select-role`,
                { role },
                {
                    headers: {
                        Authorization: `Bearer ${getRefreshToken()}`,
                    },
                }
            )
            .then((res) => res.data);
    },

    me() {
        return api
            .get("/auth/me")
            .then((res) => res.data);
    },
};

export default authApi;
