const TOKEN_KEY = "token";
const USER_KEY = "user";
const ROLE_KEY = "activeRole";

export const saveSession = ({ token, user, activeRole }) => {
    if (token)
        localStorage.setItem(TOKEN_KEY, token);

    if (user)
        localStorage.setItem(
            USER_KEY,
            JSON.stringify(user)
        );

    if (activeRole)
        localStorage.setItem(
            ROLE_KEY,
            activeRole
        );
};

export const getToken = () =>
    localStorage.getItem(TOKEN_KEY);

export const getUser = () => {
    const user = localStorage.getItem(USER_KEY);

    return user ? JSON.parse(user) : null;
};

export const getActiveRole = () =>
    localStorage.getItem(ROLE_KEY);

export const updateRole = (role) =>
    localStorage.setItem(ROLE_KEY, role);

export const clearSession = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(ROLE_KEY);
};

export const isAuthenticated = () =>
    !!getToken();