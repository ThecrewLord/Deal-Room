const ACCESS_TOKEN_KEY = "accessToken";
const REFRESH_TOKEN_KEY = "refreshToken";
const USER_KEY = "user";
const ACTIVE_ROLE_KEY = "activeRole";

export const saveSession = ({
    accessToken,
    refreshToken,
    user,
    activeRole,
}) => {
    if (accessToken !== undefined && accessToken !== null) {
        localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    }

    if (refreshToken !== undefined && refreshToken !== null) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }

    if (user !== undefined && user !== null) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
    }

    if (activeRole !== undefined && activeRole !== null) {
        localStorage.setItem(ACTIVE_ROLE_KEY, activeRole);
    }
};

export const getAccessToken = () =>
    localStorage.getItem(ACCESS_TOKEN_KEY);

export const getRefreshToken = () =>
    localStorage.getItem(REFRESH_TOKEN_KEY);

export const getUser = () => {
    const value = localStorage.getItem(USER_KEY);

    if (!value) {
        return null;
    }

    try {
        return JSON.parse(value);
    } catch {
        return null;
    }
};

export const getActiveRole = () =>
    localStorage.getItem(ACTIVE_ROLE_KEY);

export const updateActiveRole = (role) => {
    if (role === undefined || role === null) {
        localStorage.removeItem(ACTIVE_ROLE_KEY);
        return;
    }

    localStorage.setItem(ACTIVE_ROLE_KEY, role);
};

export const clearSession = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(ACTIVE_ROLE_KEY);
};