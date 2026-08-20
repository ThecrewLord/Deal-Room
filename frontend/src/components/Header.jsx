import {
    Search,
    Bell,
    ChevronDown,
    Plus,
    HelpCircle,
    X,
} from "lucide-react";

import {
    useLocation,
    useNavigate,
} from "react-router-dom";

import {
    useEffect,
    useState,
} from "react";

import { useAuth } from "../context/AuthContext";

import "../styles/header.css";

const pageTitles = {
    "/dashboard": "Dashboard",
    "/opportunities": "Opportunities",
    "/accounts": "Accounts",
    "/stakeholders": "Stakeholders",
    "/pocs": "POC Tracker",
    "/activity-log": "Activity Log",
    "/oem-registry": "Partner Registry",
    "/partner-registry": "Partner Registry",
    "/reports": "Reports & Analytics",
    "/data-quality": "Analytics — Data Quality",
    "/settings": "Settings",
    "/admin/users": "Users",
    "/admin/approval": "Pending Approvals",
    "/admin/roles": "Role Management",
    "/admin/access": "Access Management",
};

export default function Header() {
    const navigate = useNavigate();
    const location = useLocation();

    const {
        user,
        logout,
    } = useAuth();

    const [searchValue, setSearchValue] =
        useState("");

    const [showNotifications, setShowNotifications] =
        useState(false);

    const [showUserMenu, setShowUserMenu] =
        useState(false);

    const title =
        getPageTitle(location.pathname);

    useEffect(() => {
        setSearchValue("");
    }, [location.pathname]);

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
        <header className="app-header">
            {/* Page title */}
            <div className="header-title-container">
                <h2 className="header-title">
                    {title}
                </h2>
            </div>

            {/* Search */}
            <div className="header-search-container">
                <Search
                    size={14}
                    className="header-search-icon"
                />

                <input
                    type="text"
                    value={searchValue}
                    onChange={(event) =>
                        setSearchValue(
                            event.target.value
                        )
                    }
                    placeholder="Search opportunities, accounts..."
                    className="header-search"
                />

                {searchValue && (
                    <button
                        type="button"
                        className="header-search-clear"
                        onClick={() =>
                            setSearchValue("")
                        }
                    >
                        <X size={12} />
                    </button>
                )}
            </div>

            <div className="header-spacer" />

            {/* New opportunity */}
            <button
                type="button"
                className="header-new-button"
                onClick={() =>
                    navigate("/opportunities")
                }
            >
                <Plus size={13} />
                <span>New Opportunity</span>
            </button>

            {/* Help */}
            <button
                type="button"
                className="header-icon-button"
                title="Help"
            >
                <HelpCircle size={17} />
            </button>

            {/* Notifications */}
            <div className="header-dropdown-wrapper">
                <button
                    type="button"
                    className="header-icon-button notification-button"
                    onClick={() =>
                        setShowNotifications(
                            (value) => !value
                        )
                    }
                >
                    <Bell size={17} />

                    <span className="notification-dot" />
                </button>

                {showNotifications && (
                    <div className="header-dropdown notification-dropdown">
                        <div className="dropdown-header">
                            <strong>
                                Notifications
                            </strong>

                            <span>
                                3 new
                            </span>
                        </div>

                        <div className="notification-item">
                            <span className="notification-status blue" />

                            <div>
                                <p>
                                    New opportunity
                                    activity
                                </p>

                                <small>
                                    Recently updated
                                </small>
                            </div>
                        </div>

                        <div className="notification-item">
                            <span className="notification-status green" />

                            <div>
                                <p>
                                    POC activity
                                </p>

                                <small>
                                    Recently completed
                                </small>
                            </div>
                        </div>

                        <div className="notification-item">
                            <span className="notification-status orange" />

                            <div>
                                <p>
                                    Pipeline update
                                </p>

                                <small>
                                    Requires attention
                                </small>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* User */}
            <div className="header-dropdown-wrapper">
                <button
                    type="button"
                    className="header-user-button"
                    onClick={() =>
                        setShowUserMenu(
                            (value) => !value
                        )
                    }
                >
                    <div className="header-avatar">
                        {getInitials(
                            user?.full_name
                        )}
                    </div>

                    <div className="header-user-info">
                        <span className="header-user-name">
                            {user?.full_name ||
                                "User"}
                        </span>

                        <span className="header-user-role">
                            {user?.active_role ||
                                "User"}
                        </span>
                    </div>

                    <ChevronDown
                        size={14}
                        className="header-user-chevron"
                    />
                </button>

                {showUserMenu && (
                    <div className="header-dropdown user-dropdown">
                        <button
                            type="button"
                            onClick={() =>
                                navigate(
                                    "/settings"
                                )
                            }
                        >
                            Settings
                        </button>

                        <button
                            type="button"
                            className="logout-option"
                            onClick={
                                handleLogout
                            }
                        >
                            Logout
                        </button>
                    </div>
                )}
            </div>
        </header>
    );
}

function getPageTitle(pathname) {
    if (
        pathname.startsWith(
            "/opportunity/"
        )
    ) {
        return "Opportunities";
    }

    return (
        pageTitles[pathname] ||
        "Deal Room"
    );
}

function getInitials(name) {
    if (!name) {
        return "U";
    }

    return name
        .trim()
        .split(/\s+/)
        .map((part) => part[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();
}