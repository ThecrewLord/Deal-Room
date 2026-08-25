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
import Opportunities from "./pages/Opportunities";
import Accounts from "./pages/Accounts";
import Pocs from "./pages/Pocs";
import Stakeholders from "./pages/Stakeholders";
import OemRegistry from "./pages/OemRegistry";
import SalesManagerReview from "./pages/SalesManagerReview";
import SalesManagerTeamPerformance from "./pages/SalesManagerTeamPerformance";
import SalesManagerEmployeePerformance from "./pages/SalesManagerEmployeePerformance";
import PreSalesAssignment from "./pages/PreSalesAssignment";
import PreSalesManagerTeamPerformance from "./pages/PreSalesManagerTeamPerformance";
import PreSalesManagerEmployeePerformance from "./pages/PreSalesManagerEmployeePerformance";

import UserApproval from "./pages/admin/UserApproval";
import UserManagement from "./pages/admin/UserManagement";
import RoleManagement from "./pages/admin/RoleManagement";
import AccessManagement from "./pages/admin/AccessManagement";


import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRoute from "./routes/RoleRoute";
import { ROLES } from "./auth/roles";

function Unauthorized() {
    return <h2>Unauthorized</h2>;
}

function HomeRedirect() {
    const {
        isAuthenticated,
        activeRole,
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
                        <RoleRoute
                            roles={[
                                ROLES.ADMIN,
                                ROLES.SALES_EXECUTIVE,
                                ROLES.SALES_MANAGER,
                                ROLES.PRE_SALES_MANAGER,
                                ROLES.SOLUTION_ENGINEER,
                            ]}
                        >
                            <Dashboard />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/opportunities"
                element={
                    <Layout>
                        <RoleRoute
                            roles={[
                                ROLES.SALES_EXECUTIVE,
                                ROLES.SALES_MANAGER,
                                ROLES.PRE_SALES_MANAGER,
                                ROLES.SOLUTION_ENGINEER,
                            ]}
                        >
                            <Opportunities />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/accounts"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.SALES_EXECUTIVE, ROLES.SALES_MANAGER]}>
                            <Accounts />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/pocs"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.SOLUTION_ENGINEER]}>
                            <Pocs />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/stakeholders"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.SOLUTION_ENGINEER]}>
                            <Stakeholders />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/oem-registry"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.SOLUTION_ENGINEER]}>
                            <OemRegistry />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/sales-manager/review"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.SALES_MANAGER]}>
                            <SalesManagerReview />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/sales-manager/team-performance"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.SALES_MANAGER]}>
                            <SalesManagerTeamPerformance />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/sales-manager/team-performance/:employeeId"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.SALES_MANAGER]}>
                            <SalesManagerEmployeePerformance />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/pre-sales/assignments"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.PRE_SALES_MANAGER]}>
                            <PreSalesAssignment />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/pre-sales/team-performance"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.PRE_SALES_MANAGER]}>
                            <PreSalesManagerTeamPerformance />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/pre-sales/team-performance/:employeeId"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.PRE_SALES_MANAGER]}>
                            <PreSalesManagerEmployeePerformance />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/opportunity/:id"
                element={
                    <Layout>
                        <RoleRoute
                            roles={[
                                ROLES.SALES_EXECUTIVE,
                                ROLES.SALES_MANAGER,
                                ROLES.PRE_SALES_MANAGER,
                                ROLES.SOLUTION_ENGINEER,
                            ]}
                        >
                            <OpportunityDetail />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/admin/approval"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.ADMIN]}>
                            <UserApproval />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/admin/users"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.ADMIN]}>
                            <UserManagement />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/admin/roles"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.ADMIN]}>
                            <RoleManagement />
                        </RoleRoute>
                    </Layout>
                }
            />

            <Route
                path="/admin/access"
                element={
                    <Layout>
                        <RoleRoute roles={[ROLES.ADMIN]}>
                            <AccessManagement />
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
