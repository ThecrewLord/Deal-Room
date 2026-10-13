import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { AVAILABLE_ROLES } from "../auth/roles";

export default function UserMenu() {
    const navigate = useNavigate();

    const {
        user,
        activeRole,
        selectRole,
        logout,
    } = useAuth();

    const [switching, setSwitching] = useState(false);
    const [error, setError] = useState("");

    const availableRoles = (user?.roles || []).filter((role) =>
        AVAILABLE_ROLES.includes(role)
    );

    const handleRoleChange = async (event) => {
        const role = event.target.value;

        if (!role || role === activeRole || switching) {
            return;
        }

        setSwitching(true);
        setError("");

        try {
            await selectRole(role);
            navigate("/dashboard", { replace: true });
        } catch (err) {
            setError(
                err?.response?.data?.message ||
                err?.message ||
                "Unable to switch role."
            );
        } finally {
            setSwitching(false);
        }
    };

    const handleLogout = async () => {
        try {
            await logout();
        } finally {
            navigate("/login", {
                replace: true,
            });
        }
    };

    return (
        <div className="user-menu">
            <span>
                {user?.full_name}
            </span>

            {availableRoles.length > 1 && (
                <select
                    value={activeRole || ""}
                    onChange={handleRoleChange}
                    disabled={switching}
                    aria-label="Switch active role"
                >
                    {availableRoles.map((role) => (
                        <option key={role} value={role}>
                            {role}
                        </option>
                    ))}
                </select>
            )}

            {error && (
                <span
                    role="alert"
                    style={{
                        color: "var(--color-danger)",
                        fontSize: "12px",
                    }}
                >
                    {error}
                </span>
            )}

            <button
                onClick={handleLogout}
                disabled={switching}
            >
                Logout
            </button>
        </div>
    );
}
