import axios from "axios";
import API_BASE_URL from "../config/api";

import {
    getAccessToken,
    getRefreshToken,
    saveSession,
    clearSession,
} from "../auth/authStorage";

const api = axios.create({
    baseURL: API_BASE_URL,
});

let isRefreshing = false;

let failedQueue = [];

const processQueue = (
    error,
    token = null
) => {
    failedQueue.forEach(
        ({ resolve, reject }) => {
            if (error) {
                reject(error);
            } else {
                resolve(token);
            }
        }
    );

    failedQueue = [];
};

api.interceptors.request.use(

    (config) => {
        const token =
            getAccessToken();

        if (token) {
            config.headers.Authorization =
                `Bearer ${token}`;
        }

        return config;
    }
);





api.interceptors.response.use(
    (response) => response,

    async (error) => {

        const originalRequest =
            error.config;

        const message = error.response?.data?.message || "";
        if (error.response?.status === 409 && error.response?.data) {
            error.response.data.message = "This record was changed by another user. Refresh and try again.";
        }
        if (error.response?.status === 403 && message.toLowerCase().includes("revoked")) {
            clearSession();
            window.location.replace("/revoked");
            return Promise.reject(error);
        }
        if (error.response?.status === 403 && (message.toLowerCase().includes("stale") || message.toLowerCase().includes("no longer assigned"))) {
            clearSession();
            window.location.replace("/login");
            return Promise.reject(error);
        }

        const authEndpoints = [
            "/auth/login",
            "/auth/signup",
            "/auth/refresh",
        ];

        if (
            !error.response ||
            error.response.status !== 401 ||
            originalRequest._retry ||
            authEndpoints.some(endpoint =>
                originalRequest.url?.includes(endpoint)
            )
        ) {
            return Promise.reject(error);
        }

        originalRequest._retry = true;

        if (isRefreshing) {
            return new Promise(
                (resolve, reject) => {
                    failedQueue.push({
                        resolve,
                        reject,
                    });
                }
            ).then((token) => {
                originalRequest.headers.Authorization =
                    `Bearer ${token}`;

                return api(
                    originalRequest
                );
            });
        }

        const refreshToken = getRefreshToken();

        if (!refreshToken) {
            clearSession();
            return Promise.reject(error);
        }

        isRefreshing = true;

        try {
            const response =
                await axios.post(
                    `${API_BASE_URL}/auth/refresh`,
                    {},
                    {
                        headers: {
                            Authorization: `Bearer ${getRefreshToken()}`,
                        },
                    }
                );

            const {
                access_token,
                active_role,
            } = response.data;

            saveSession({
                accessToken:
                    access_token,
                activeRole:
                    active_role,
            });

            processQueue(
                null,
                access_token
            );

            originalRequest.headers.Authorization =
                `Bearer ${access_token}`;

            return api(originalRequest);
        } catch (refreshError) {
            processQueue(
                refreshError,
                null
            );

            clearSession();
            const refreshMessage = refreshError.response?.data?.message || "";
            window.location.replace(refreshMessage.toLowerCase().includes("revoked") ? "/revoked" : "/login");

            return Promise.reject(
                refreshError
            );
        } finally {
            isRefreshing = false;
        }
    }
);

export default api;