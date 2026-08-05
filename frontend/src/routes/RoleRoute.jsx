import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
    getActiveRole,
    isAuthenticated,
} 
 from "../auth/authStorage";

// export default function RoleRoute({

//     children,

//     roles,

// }) {

//     if (!isAuthenticated()) {

//         return <Navigate to="/login" replace />;

//     }

//     const role = getActiveRole();

//     if (!roles.includes(role)) {

//         return (

//             <Navigate

//                 to="/unauthorized"

//                 replace

//             />

//         );

//     }

//     return children;

// }

export default function RoleRoute({

    role,

    children,

}) {

    const { user } = useAuth();

    if (!user) {

        return (
            <Navigate
                replace
                to="/login"
            />
        );

    }

    if (user.active_role !== role) {

        return (
            <Navigate
                replace
                to="/dashboard"
            />
        );

    }

    return children;

}