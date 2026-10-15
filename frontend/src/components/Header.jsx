import { Search, Bell, ChevronDown, Plus, HelpCircle, X, CheckCheck, ArrowUpRight } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getNotifications, markNotificationRead, markAllNotificationsRead } from "../api/notificationApi";
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
    const [notificationError, setNotificationError] = useState("");
    const [markingAllRead, setMarkingAllRead] = useState(false);
    const notificationWrapperRef = useRef(null);
    const [searchResults, setSearchResults] = useState([]);
    const [searching, setSearching] = useState(false);
    const [showSearchResults, setShowSearchResults] = useState(false);
    const searchTimer = useRef(null);

    const title = getPageTitle(location.pathname);
    const canCreateOpportunity = activeRole && activeRole !== ROLES.ADMIN;

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
                setSearchResults(results?.items || results || []);
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
        setNotifications([]);
        setNotificationError("");
        getNotifications()
            .then((items) => mounted && setNotifications(Array.isArray(items) ? items : []))
            .catch(() => {
                if (mounted) {
                    setNotifications([]);
                    setNotificationError("Unable to load notifications.");
                }
            });
        return () => { mounted = false; };
    }, [location.pathname, activeRole]);

    useEffect(() => {
        if (!showNotifications) return undefined;
        const handlePointerDown = (event) => {
            if (!notificationWrapperRef.current?.contains(event.target)) {
                setShowNotifications(false);
            }
        };
        const handleKeyDown = (event) => {
            if (event.key === "Escape") setShowNotifications(false);
        };
        document.addEventListener("mousedown", handlePointerDown);
        document.addEventListener("keydown", handleKeyDown);
        return () => {
            document.removeEventListener("mousedown", handlePointerDown);
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [showNotifications]);

    const openSearchResult = (result) => {
        setShowSearchResults(false);
        setSearchValue("");
        if (result.type === "opportunity") navigate(`/opportunity/${result.id}`);
        else if (result.type === "account") navigate("/accounts");
        else if (result.type === "poc") navigate("/pocs");
        else if (["stakeholder", "oem", "activity", "follow-up", "delivery-project"].includes(result.type)) navigate("/opportunities");
    };

    const handleLogout = async () => {
        try { await logout(); } finally { navigate("/login", { replace: true }); }
    };

    const unreadCount = notifications.filter((item) => !item.is_read).length;

    const markOneRead = async (notification) => {
        if (notification.is_read) return true;
        try {
            await markNotificationRead(notification.notification_id);
            setNotifications((items) => items.map((item) =>
                item.notification_id === notification.notification_id ? { ...item, is_read: true } : item
            ));
            setNotificationError("");
            return true;
        } catch {
            setNotificationError("Unable to mark this notification as read.");
            return false;
        }
    };

    const markAllRead = async () => {
        if (markingAllRead || unreadCount === 0) return;
        setMarkingAllRead(true);
        setNotificationError("");
        try {
            await markAllNotificationsRead();
            setNotifications((items) => items.map((item) => ({ ...item, is_read: true })));
        } catch (error) {
            setNotificationError(error?.response?.data?.message || "Unable to mark notifications as read.");
        } finally {
            setMarkingAllRead(false);
        }
    };

    const notificationDestination = (notification) => {
        if (!notification.entity_id) return null;
        switch ((notification.entity_type || "").toLowerCase()) {
            case "opportunity": return `/opportunity/${notification.entity_id}`;
            case "poc": return "/pocs";
            case "account": return "/accounts";
            case "stakeholder": return "/stakeholders";
            default: return null;
        }
    };

    const openNotification = async (notification) => {
        await markOneRead(notification);
        const destination = notificationDestination(notification);
        setShowNotifications(false);
        if (destination) navigate(destination);
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
                        placeholder="Search opportunities, accounts, or POCs..."
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

            <div className="header-dropdown-wrapper notification-wrapper" ref={notificationWrapperRef}>
                <button
                    type="button"
                    className="header-icon-button notification-button"
                    onClick={() => setShowNotifications((value) => !value)}
                    aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}
                    aria-expanded={showNotifications}
                    aria-controls="notification-dropdown"
                >
                    <Bell size={17} />
                    {unreadCount > 0 && <span className="notification-dot" aria-hidden="true" />}
                </button>
                {showNotifications && (
                    <section className="header-dropdown notification-dropdown" id="notification-dropdown" role="dialog" aria-label="Notifications">
                        <div className="notification-panel-header">
                            <div>
                                <h3>Notifications</h3>
                                <p>{unreadCount ? `${unreadCount} unread` : "You're all caught up"}</p>
                            </div>
                            <button type="button" className="notification-mark-all" onClick={markAllRead} disabled={!unreadCount || markingAllRead}>
                                <CheckCheck size={13} /> {markingAllRead ? "Marking…" : "Mark all as read"}
                            </button>
                        </div>
                        {notificationError && <div className="notification-panel-error" role="alert">{notificationError}</div>}
                        {!notifications.length ? (
                            <div className="notification-empty">
                                <span className="notification-empty-icon"><Bell size={18} /></span>
                                <strong>No notifications yet</strong>
                                <p>Workflow updates will appear here.</p>
                            </div>
                        ) : (
                            <div className="notification-list">
                                {notifications.slice(0, 8).map((notification) => {
                                    const destination = notificationDestination(notification);
                                    return (
                                        <article key={notification.notification_id} className={`notification-row ${notification.is_read ? "is-read" : "is-unread"}`}>
                                            <span className={`notification-status ${notification.is_read ? "read" : "blue"}`} aria-hidden="true" />
                                            <button type="button" className="notification-open" onClick={() => openNotification(notification)} aria-label={`${destination ? "Open" : "View"} notification: ${notification.message}`}>
                                                <span className="notification-message">{notification.message}</span>
                                                <small>{formatNotificationTime(notification.created_at)}</small>
                                            </button>
                                            <div className="notification-row-actions">
                                                {destination && <button type="button" className="notification-open-link" onClick={() => openNotification(notification)} aria-label="Open related record"><ArrowUpRight size={14} /></button>}
                                                {!notification.is_read && <button type="button" className="notification-mark-one" onClick={() => markOneRead(notification)} aria-label="Mark notification as read">Mark read</button>}
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        )}
                    </section>
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

function formatNotificationTime(value) {
    if (!value) return "Time unavailable";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Time unavailable";
    const deltaSeconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
    if (deltaSeconds < 60) return "Just now";
    if (deltaSeconds < 3600) return `${Math.floor(deltaSeconds / 60)}m ago`;
    if (deltaSeconds < 86400) return `${Math.floor(deltaSeconds / 3600)}h ago`;
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: date.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined });
}

function getPageTitle(pathname) {
    if (pathname.startsWith("/opportunity/")) return "Opportunity Detail";
    return pageTitles[pathname] || "Deal Room";
}

function getInitials(name) {
    if (!name) return "U";
    return name.trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}
