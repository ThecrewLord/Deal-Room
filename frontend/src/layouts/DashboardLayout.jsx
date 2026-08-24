import Header from "../components/Header";
import Sidebar from "../components/Sidebar";


export default function DashboardLayout({
    children,
}) {
    return (
        <div className="dashboard-layout">
            <Sidebar />

            <div className="dashboard-main-container">
                <Header />

                <main className="dashboard-content">
                    {children}
                </main>
            </div>
        </div>
    );
}