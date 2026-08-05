import Header from "../components/Header";
import Sidebar from "../components/Sidebar";

import "../styles/dashboard.css";

export default function DashboardLayout({

    children,

}) {

    return (

        <div className="dashboard-layout">

            <Header />

            <div className="dashboard-body">

                <Sidebar />

                <main className="dashboard-content">

                    {children}

                </main>

            </div>

        </div>

    );

}