import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function UserMenu() {
    const navigate = useNavigate();

    const {
        user,
        logout,
    } = useAuth();

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

            <button
                onClick={handleLogout}
            >
                Logout
            </button>
        </div>
    );
}