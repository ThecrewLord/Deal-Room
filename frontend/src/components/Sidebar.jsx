import {
    LayoutDashboard,
    Building2,
    Target,
    Users,
    FlaskConical,
    Activity,
    Handshake,
    BarChart3,
    ShieldCheck,
    Settings,
    ChevronRight,
} from "lucide-react";

import { NavLink } from "react-router-dom";

import navigation from "../config/navigation";
import { getActiveRole } from "../auth/authStorage";

import "../styles/sidebar.css";

const iconMap = {
    Dashboard: LayoutDashboard,
    Opportunities: Target,
    Accounts: Building2,
    Stakeholders: Users,
    POCs: FlaskConical,
    "POC Tracker": FlaskConical,
    "Activity Log": Activity,
    "OEM Registry": Handshake,
    "Partner Registry": Handshake,
    Reports: BarChart3,
    Analytics: BarChart3,
    "Pending Approvals": ShieldCheck,
    Users: Users,
    "Role Management": Users,
    "Access Management": ShieldCheck,
    Settings,
};

function getIcon(name) {
    return iconMap[name] || LayoutDashboard;
}

function getNavigationItems(role) {
    const menu = navigation[role] || [];

    return menu;
}

export default function Sidebar() {
    const role = getActiveRole();

    const menu = getNavigationItems(role);

    const mainItems = menu.filter(
        (item) =>
            ![
                "Reports",
                "Analytics",
                "Activity Log",
                "Settings",
            ].includes(item.name)
    );

    const intelligenceItems = menu.filter(
        (item) =>
            [
                "Reports",
                "Analytics",
                "Activity Log",
                "Settings",
            ].includes(item.name)
    );

    return (
        <aside className="app-sidebar">
            {/* Brand */}
            <div className="sidebar-brand">
                <div className="sidebar-brand-icon">
                    <BarChart3 size={17} />
                </div>

                <div className="sidebar-brand-text">
                    <span className="sidebar-brand-name">
                        Deal Room
                    </span>

                    <span className="sidebar-brand-subtitle">
                        Sales Intelligence
                    </span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="sidebar-navigation">
                {mainItems.length > 0 && (
                    <div className="sidebar-section">
                        <p className="sidebar-section-title">
                            Main Menu
                        </p>

                        {mainItems.map((item) => {
                            const Icon = getIcon(item.name);

                            return (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    className={({ isActive }) =>
                                        `sidebar-link ${
                                            isActive
                                                ? "active"
                                                : ""
                                        }`
                                    }
                                >
                                    <Icon
                                        size={16}
                                        className="sidebar-link-icon"
                                    />

                                    <span className="sidebar-link-label">
                                        {item.name}
                                    </span>

                                    <ChevronRight
                                        size={14}
                                        className="sidebar-link-arrow"
                                    />
                                </NavLink>
                            );
                        })}
                    </div>
                )}

                {intelligenceItems.length > 0 && (
                    <div className="sidebar-section sidebar-intelligence">
                        <p className="sidebar-section-title">
                            Intelligence
                        </p>

                        {intelligenceItems.map((item) => {
                            const Icon = getIcon(item.name);

                            return (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    className={({ isActive }) =>
                                        `sidebar-link ${
                                            isActive
                                                ? "active"
                                                : ""
                                        }`
                                    }
                                >
                                    <Icon
                                        size={16}
                                        className="sidebar-link-icon"
                                    />

                                    <span className="sidebar-link-label">
                                        {item.name}
                                    </span>

                                    <ChevronRight
                                        size={14}
                                        className="sidebar-link-arrow"
                                    />
                                </NavLink>
                            );
                        })}
                    </div>
                )}
            </nav>

            {/* Role */}
            <div className="sidebar-user-area">
                <div className="sidebar-user">
                    <div className="sidebar-avatar">
                        {getInitials(role)}
                    </div>

                    <div className="sidebar-user-info">
                        <p className="sidebar-user-name">
                            {role || "User"}
                        </p>

                        <p className="sidebar-user-role">
                            Active Role
                        </p>
                    </div>
                </div>
            </div>
        </aside>
    );
}

function getInitials(value) {
    if (!value) {
        return "U";
    }

    return value
        .split(" ")
        .map((word) => word[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();
}