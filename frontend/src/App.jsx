import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/auth/Login";
import Signup from "./pages/auth/Signup";
import PendingAccess from "./pages/auth/PendingAccess";
import RevokedAccess from "./pages/auth/RevokedAccess";
import RoleSelection from "./pages/auth/RoleSelection";

import Dashboard from "./pages/dashboard/dashboard";
import DashboardLayout from "./layouts/DashboardLayout";

import OpportunityDetail from "./pages/OpportunityDetail";

import UserApproval from "./pages/admin/UserApproval";
import UserManagement from "./pages/admin/UserManagement";

import ComingSoon from "./pages/common/ComingSoon";

import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRoute from "./routes/RoleRoute";

function Unauthorized() {
    return <h2>Unauthorized</h2>;
}

function HomeRedirect() {
    const {
        isAuthenticated,
        loading,
    } = useAuth();

    if (loading) {
        return null;
    }

    return (
        <Navigate
            replace
            to={
                isAuthenticated
                    ? "/dashboard"
                    : "/login"
            }
        />
    );
}

function Layout({ children }) {
    return (
        <ProtectedRoute>
            <DashboardLayout>
                {children}
            </DashboardLayout>
        </ProtectedRoute>
    );
}

export default function App() {
    return (
        <Routes>

            <Route
                path="/"
                element={<HomeRedirect />}
            />

            <Route
                path="/login"
                element={<Login />}
            />

            <Route
                path="/signup"
                element={<Signup />}
            />

            <Route
                path="/pending"
                element={<PendingAccess />}
            />

            <Route
                path="/revoked"
                element={<RevokedAccess />}
            />

            <Route
                path="/select-role"
                element={<RoleSelection />}
            />

            <Route
                path="/unauthorized"
                element={<Unauthorized />}
            />

            <Route
                path="/dashboard"
                element={
                    <Layout>
                        <Dashboard />
                    </Layout>
                }
            />

            <Route
                path="/opportunity/:id"
                element={
                    <Layout>
                        <OpportunityDetail />
                    </Layout>
                }
            />

            <Route
                path="/admin/approval"
                element={
                    <Layout>
                        <RoleRoute roles={["Admin"]}>
                            <UserApproval />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/admin/users"
                element={
                    <Layout>
                        <RoleRoute roles={["Admin"]}>
                            <UserManagement />
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
                path="*"
                element={
                    <Navigate
                        replace
                        to="/"
                    />
                }
            />

        </Routes>
    );
}
