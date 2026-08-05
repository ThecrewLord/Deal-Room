import { createContext, useContext, useEffect, useState } from "react";
import authService from "../auth/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    async function restoreSession() {
        try {
            const me = await authService.me();
            setUser(me);
        } catch {
            authService.logoutLocal();
            setUser(null);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        restoreSession();
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                setUser,
                loading,
                restoreSession,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}