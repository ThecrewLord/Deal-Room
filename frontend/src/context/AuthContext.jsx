import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";

import authService from "../auth/authService";

import {
    saveSession,
    clearSession,
    getAccessToken,
    updateActiveRole,
} from "../auth/authStorage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);

    const [activeRole, setActiveRole] = useState(null);

    const [loading, setLoading] = useState(true);


    const restoreSession = useCallback(async () => {
        const accessToken = getAccessToken();

        if (!accessToken) {
            setLoading(false);
            return;
        }

        try {

            const me = await authService.me();

            setUser(me);

            const role =
                me.active_role ?? null;

            setActiveRole(role);

            if (role) {
                updateActiveRole(role);
            }

        } catch {

            clearSession();

            setUser(null);
            setActiveRole(null);

        } finally {

            setLoading(false);

        }

    }, []);


    useEffect(() => {
        restoreSession();
    }, [restoreSession]);


    const login = useCallback(async (credentials) => {
        const session = await authService.login(credentials);

        if (session.requires_role_selection) {
            return session;
        }

        saveSession({
            accessToken: session.access_token,
            refreshToken: session.refresh_token,
            user: session.user,
            activeRole: session.active_role,
            // activeRole  : session.user?.roles?.[0] ?? null,
        });

        setUser(session.user);

        setActiveRole(
            session.active_role ?? null
        );

        return session;
    }, []);


    const selectRole = useCallback(async (role) => {
        const session =
            await authService.selectRole(role);

        saveSession({
            accessToken:
                session.access_token,
            refreshToken:
                session.refresh_token,
            user:
                session.user,
            activeRole:
                role,
        });

        setUser(session.user);

        setActiveRole(
            session.active_role ?? role
        );

        return session;
    }, []);


    const logout = useCallback(async () => {
        try {
            await authService.logout();
        } finally {
            clearSession();

            setUser(null);

            setActiveRole(null);
        }
    }, []);


    const refreshUser = useCallback(async () => {
        const me =
            await authService.me();

        setUser(me);

        const role =
            me.active_role ?? null;

        setActiveRole(role);

        if (role) {
            updateActiveRole(role);
        }

        return me;
    }, []);


    const value = useMemo(
        () => ({
            user,

            activeRole,

            loading,

            isAuthenticated:
                !!user,

            login,

            selectRole,

            logout,

            refreshUser,

            restoreSession,

            setUser,

            setActiveRole,
        }),
        [
            user,
            activeRole,
            loading,
            login,
            logout,
            refreshUser,
            restoreSession,
        ]
    );

    
    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context =
        useContext(AuthContext);

    if (!context) {
        throw new Error(
            "useAuth must be used within AuthProvider."
        );
    }

    return context;
}