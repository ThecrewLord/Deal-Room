import axios from "axios";

import {
    getAccessToken,
    getRefreshToken,
    saveSession,
    clearSession,
} from "../auth/authStorage";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
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
                    `${import.meta.env.VITE_API_URL}/auth/refresh`,
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

            window.location.replace(
                "/login"
            );

            return Promise.reject(
                refreshError
            );
        } finally {
            isRefreshing = false;
        }
    }
);

export default api;