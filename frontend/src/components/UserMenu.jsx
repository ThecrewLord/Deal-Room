import { useNavigate } from "react-router-dom";

import { getUser } from "../auth/authStorage";
import { logout } from "../auth/authService";

export default function UserMenu() {

    const navigate = useNavigate();

    const user = getUser();

    const handleLogout = async () => {

        await logout();

        navigate("/login", {
            replace: true,
        });

    };

    return (

        <div className="user-menu">

            <span>

                {user?.firstName} {user?.lastName}

            </span>

            <button
                onClick={handleLogout}
            >

                Logout

            </button>

        </div>

    );

}