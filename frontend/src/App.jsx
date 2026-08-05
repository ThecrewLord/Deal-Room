import { Routes, Route } from "react-router-dom";
import Login from "./pages/auth/Login";
import Signup from "./pages/auth/Signup";
import PendingAccess from "./pages/auth/PendingAccess";
import RevokedAccess from "./pages/auth/RevokedAccess";
import RoleSelection from "./pages/auth/RoleSelection";
import DashboardLayout from "./layouts/DashboardLayout";
import Dashboard from "./pages/dashboard/Dashboard";
import ComingSoon from "./pages/common/ComingSoon";
import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRoute from "./routes/RoleRoute";
import OpportunityDetail from "./pages/OpportunityDetail";
import { Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import UserApproval from "./pages/admin/UserApproval";
import UserManagement from "./pages/admin/UserManagement";
import RoleRoute from "./routes/RoleRoute";

function Home() {

    return <h2>Collaborating Opportunities</h2>;

}

function Unauthorized() {

    return <h2>Unauthorized</h2>;

}

const Layout = ({ children }) => (

    <ProtectedRoute>

        <DashboardLayout>

            {children}

        </DashboardLayout>

    </ProtectedRoute>

);


function HomeRedirect() {

    const { user, loading } = useAuth();

    if (loading) return null;

    return (
        <Navigate
            replace
            to={
                user
                    ? "/dashboard"
                    : "/login"
            }
        />
    );
}

export default function App() {

    return (

        <Routes>

            <Route path="/" element={<HomeRedirect />} />

            <Route path="/login" element={<Login />} />

            <Route path="/signup" element={<Signup />} />

            <Route path="/pending" element={<PendingAccess />} />

            <Route path="/revoked" element={<RevokedAccess />} />

            <Route path="/select-role" element={<RoleSelection />} />

            <Route path="/unauthorized" element={<Unauthorized />} />

            <Route

                path="/dashboard"

                element={

                    <Layout>

                        <Dashboard />

                    </Layout>

                }

            />

            <Route

                path="/admin/users"

                element={

                    <Layout>

                        <RoleRoute roles={["Admin"]}>

                            <ComingSoon title="Pending Users" />

                        </RoleRoute>

                    </Layout>

                }

            />

            <Route

                path="/admin/roles"

                element={

                    <Layout>

                        <RoleRoute roles={["Admin"]}>

                            <ComingSoon title="Assign Roles" />

                        </RoleRoute>

                    </Layout>

                }

            />

            <Route

                path="/admin/access"

                element={

                    <Layout>

                        <RoleRoute roles={["Admin"]}>

                            <ComingSoon title="Access Management" />

                        </RoleRoute>

                    </Layout>

                }

            />

            <Route

                path="/opportunity/:id"
                element={<OpportunityDetail />}

            />

            <Route

                path="/admin/approval"

                element={

                    <ProtectedRoute>

                        <RoleRoute role="Admin">

                            <UserApproval />

                        </RoleRoute>

                    </ProtectedRoute>

                }

            />

            <Route

                path="/admin/users"

                element={

                    <ProtectedRoute>

                        <RoleRoute role="Admin">

                            <UserManagement />

                        </RoleRoute>

                    </ProtectedRoute>

                }

            />

        </Routes>

    );

}