import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RoleRoute({
    children,
    roles,
}) {
    const {
        loading,
        isAuthenticated,
        activeRole,
    } = useAuth();

    if (loading) {
        return (
            <div className="page-loading">
                Loading...
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <Navigate
                to="/login"
                replace
            />
        );
    }

    if (!roles.includes(activeRole)) {
        return (
            <Navigate
                to="/unauthorized"
                replace
            />
        );
    }

    return children;
}