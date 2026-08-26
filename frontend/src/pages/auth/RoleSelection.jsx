import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { AVAILABLE_ROLES } from "../../auth/roles";

import "../../styles/auth.css";

export default function RoleSelection() {
    const navigate = useNavigate();
    const { selectRole } = useAuth();

    const storedResponse =
        sessionStorage.getItem("login_response");

    let loginResponse = null;

    try {
        loginResponse = storedResponse
            ? JSON.parse(storedResponse)
            : null;
    } catch {
        loginResponse = null;
    }

    const [role, setRole] = useState("");
    const [error, setError] = useState("");

    if (!loginResponse?.roles?.length) {
        navigate("/login", { replace: true });
        return null;
    }

    // The backend is authoritative; this filter only prevents stale/unknown
    // role values from becoming selectable UI options.
    const assignedRoles = loginResponse.roles.filter(
        (candidate) => AVAILABLE_ROLES.includes(candidate)
    );

    async function submit() {
        if (!role) {
            setError("Please select a role.");
            return;
        }

        if (!assignedRoles.includes(role)) {
            setError("Please select an assigned role.");
            return;
        }

        try {
            await selectRole(role);

            sessionStorage.removeItem("login_response");

            navigate("/dashboard", { replace: true });
        } catch (err) {
            const message = err.response?.data?.message || "Unable to select role.";
            if (message.toLowerCase().includes("revoked")) {
                sessionStorage.removeItem("login_response");
                navigate("/revoked", { replace: true });
                return;
            }
            if (message.toLowerCase().includes("stale")) {
                sessionStorage.removeItem("login_response");
                navigate("/login", { replace: true });
                return;
            }
            setError(message);
        }
    }

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h2>Select Role</h2>

                <div className="auth-form">
                    {assignedRoles.map((candidate) => (
                        <label key={candidate}>
                            <input
                                type="radio"
                                value={candidate}
                                checked={role === candidate}
                                onChange={() => setRole(candidate)}
                            />
                            {" "}
                            {candidate}
                        </label>
                    ))}

                    {assignedRoles.length === 0 && (
                        <p>
                            No valid roles are assigned to this account.
                        </p>
                    )}

                    {error && <p>{error}</p>}

                    <button
                        onClick={submit}
                        disabled={assignedRoles.length === 0}
                    >
                        Continue
                    </button>
                </div>
            </div>
        </div>
    );
}
