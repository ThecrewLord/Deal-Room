import { Search, Bell, ChevronDown, Plus, HelpCircle, X } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getNotifications, markNotificationRead } from "../api/notificationApi";
import { searchAuthorized } from "../api/searchApi";
import { ROLES } from "../auth/roles";
import "../styles/header.css";

const pageTitles = {
    "/dashboard": "Dashboard",
    "/opportunities": "Opportunities",
    "/accounts": "Accounts",
    "/stakeholders": "Stakeholders",
    "/pocs": "POC Tracker",
    "/oem-registry": "OEM Registry",
    "/sales-manager/review": "Review Queue",
    "/pre-sales/assignments": "Pending Technical Assignment",
        "/admin/users": "Users",
    "/admin/approval": "Pending Approvals",
    "/admin/roles": "Role Management",
    "/admin/access": "Access Management",
};

export default function Header() {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, activeRole, logout } = useAuth();
    const [searchValue, setSearchValue] = useState("");
    const [showNotifications, setShowNotifications] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [notifications, setNotifications] = useState([]);
    const [searchResults, setSearchResults] = useState([]);
    const [searching, setSearching] = useState(false);
    const [showSearchResults, setShowSearchResults] = useState(false);
    const searchTimer = useRef(null);

    const title = getPageTitle(location.pathname);
    const canCreateOpportunity = activeRole === ROLES.SALES_EXECUTIVE;

    useEffect(() => {
        setSearchValue("");
        setSearchResults([]);
        setShowSearchResults(false);
    }, [location.pathname]);

    useEffect(() => {
        if (searchTimer.current) clearTimeout(searchTimer.current);
        const query = searchValue.trim();
        if (query.length < 2 || activeRole === ROLES.ADMIN) {
            setSearchResults([]);
            setSearching(false);
            return;
        }
        setSearching(true);
        setShowSearchResults(true);
        searchTimer.current = setTimeout(async () => {
            try {
                const results = await searchAuthorized(query);
                setSearchResults(results || []);
            } catch {
                setSearchResults([]);
            } finally {
                setSearching(false);
            }
        }, 300);
        return () => searchTimer.current && clearTimeout(searchTimer.current);
    }, [searchValue, activeRole]);

    useEffect(() => {
        let mounted = true;
        getNotifications()
            .then((items) => mounted && setNotifications(items || []))
            .catch(() => mounted && setNotifications([]));
        return () => { mounted = false; };
    }, [location.pathname, activeRole]);

    const openSearchResult = (result) => {
        setShowSearchResults(false);
        setSearchValue("");
        if (result.type === "opportunity") navigate(`/opportunity/${result.id}`);
        else if (result.type === "account") navigate("/accounts");
        else if (result.type === "poc") navigate("/pocs");
    };

    const handleLogout = async () => {
        try { await logout(); } finally { navigate("/login", { replace: true }); }
    };

    const unreadCount = notifications.filter((item) => !item.is_read).length;

    const openNotification = async (notification) => {
        if (!notification.is_read) {
            try {
                await markNotificationRead(notification.notification_id);
                setNotifications((items) => items.map((item) =>
                    item.notification_id === notification.notification_id ? { ...item, is_read: true } : item
                ));
            } catch { /* The notification remains visible if marking read fails. */ }
        }
        if (notification.entity_type?.toLowerCase() === "opportunity" && notification.entity_id) {
            navigate(`/opportunity/${notification.entity_id}`);
        }
        if (notification.entity_type?.toLowerCase() === "poc" && notification.entity_id) {
            const path = "/pocs";
            navigate(path);
        }
    };

    return (
        <header className="app-header">
            <div className="header-title-container"><h2 className="header-title">{title}</h2></div>
            {activeRole !== ROLES.ADMIN && (
                <div className="header-search-container">
                    <Search size={14} className="header-search-icon" />
                    <input
                        value={searchValue}
                        onFocus={() => searchValue.trim().length >= 2 && setShowSearchResults(true)}
                        onChange={(event) => setSearchValue(event.target.value)}
                        placeholder="Search opportunities, accounts, POCs..."
                        className="header-search"
                        aria-label="Search authorized business records"
                    />
                    {searchValue && <button type="button" className="header-search-clear" onClick={() => setSearchValue("")}><X size={12} /></button>}
                    {showSearchResults && searchValue.trim().length >= 2 && (
                        <div className="header-search-results">
                            {searching && <div className="header-search-state">Searching authorized records…</div>}
                            {!searching && !searchResults.length && <div className="header-search-state">No matching authorized results.</div>}
                            {!searching && searchResults.map((result) => (
                                <button key={`${result.type}-${result.id}`} type="button" className="header-search-result" onClick={() => openSearchResult(result)}>
                                    <span className="header-search-result-type">{result.type.toUpperCase()}</span>
                                    <span className="header-search-result-content">
                                        <strong>{result.title}</strong>
                                        {result.subtitle && <small>{result.subtitle}</small>}
                                    </span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            )}
            <div className="header-spacer" />

            {canCreateOpportunity && (
                <button type="button" className="header-new-button" onClick={() => navigate("/opportunities")}>
                    <Plus size={13} /><span>New Opportunity</span>
                </button>
            )}

            <button type="button" className="header-icon-button" title="Help"><HelpCircle size={17} /></button>

            <div className="header-dropdown-wrapper">
                <button type="button" className="header-icon-button notification-button" onClick={() => setShowNotifications((value) => !value)}>
                    <Bell size={17} />
                    {unreadCount > 0 && <span className="notification-dot" />}
                </button>
                {showNotifications && (
                    <div className="header-dropdown notification-dropdown">
                        <div className="dropdown-header"><strong>Notifications</strong><span>{unreadCount} unread</span></div>
                        {!notifications.length && <div className="notification-item"><span>No notifications.</span></div>}
                        {notifications.slice(0, 8).map((notification) => (
                            <button key={notification.notification_id} type="button" className="notification-item" onClick={() => openNotification(notification)}>
                                <span className={`notification-status ${notification.is_read ? "" : "blue"}`} />
                                <div><p>{notification.message}</p><small>{notification.created_at ? new Date(notification.created_at).toLocaleString() : ""}</small></div>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="header-dropdown-wrapper">
                <button type="button" className="header-user-button" onClick={() => setShowUserMenu((value) => !value)}>
                    <div className="header-avatar">{getInitials(user?.full_name)}</div>
                    <div className="header-user-info">
                        <span className="header-user-name">{user?.full_name || "User"}</span>
                        <span className="header-user-role">{activeRole || "No active role"}</span>
                    </div>
                    <ChevronDown size={14} className="header-user-chevron" />
                </button>
                {showUserMenu && (
                    <div className="header-dropdown user-dropdown">
                        <button type="button" className="logout-option" onClick={handleLogout}>Logout</button>
                    </div>
                )}
            </div>
        </header>
    );
}

function getPageTitle(pathname) {
    if (pathname.startsWith("/opportunity/")) return "Opportunity Detail";
    return pageTitles[pathname] || "Deal Room";
}

function getInitials(name) {
    if (!name) return "U";
    return name.trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}
