import { useEffect, useMemo, useState } from "react";
import {
    Building2,
    CheckCircle2,
    Clock3,
    CalendarX2,
    Search,
    RefreshCw,
    Mail,
} from "lucide-react";

import api from "../api/axiosClient";
import { ROLES } from "../auth/roles";
import { useAuth } from "../context/AuthContext";

export default function OemRegistry() {
    const { activeRole } = useAuth();

    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [productFilter, setProductFilter] = useState("all");

    useEffect(() => {
        let mounted = true;

        setLoading(true);
        setError("");

        api.get("/oem/")
            .then((response) => {
                if (mounted) {
                    setItems(response.data || []);
                }
            })
            .catch((err) => {
                if (mounted) {
                    setError(
                        err?.response?.data?.message ||
                        "Unable to load OEM registry."
                    );
                }
            })
            .finally(() => {
                if (mounted) {
                    setLoading(false);
                }
            });

        return () => {
            mounted = false;
        };
    }, [activeRole]);

    const refresh = () => {
        setLoading(true);
        setError("");

        api.get("/oem/")
            .then((response) => {
                setItems(response.data || []);
            })
            .catch((err) => {
                setError(
                    err?.response?.data?.message ||
                    "Unable to load OEM registry."
                );
            })
            .finally(() => {
                setLoading(false);
            });
    };

    const products = useMemo(() => {
        return [
            ...new Set(
                items
                    .map((item) => item.product_name)
                    .filter(Boolean)
            ),
        ];
    }, [items]);

    const filteredItems = useMemo(() => {
        const query = search.trim().toLowerCase();

        return items.filter((item) => {
            const partner = String(
                item.partner_name || ""
            ).toLowerCase();

            const product = String(
                item.product_name || ""
            ).toLowerCase();

            const contact = String(
                item.contact_person || ""
            ).toLowerCase();

            const email = String(
                item.email || ""
            ).toLowerCase();

            const status = String(
                item.status || ""
            ).toLowerCase();

            const matchesSearch =
                !query ||
                partner.includes(query) ||
                product.includes(query) ||
                contact.includes(query) ||
                email.includes(query);

            const matchesStatus =
                statusFilter === "all" ||
                status === statusFilter;

            const matchesProduct =
                productFilter === "all" ||
                product === productFilter;

            return (
                matchesSearch &&
                matchesStatus &&
                matchesProduct
            );
        });
    }, [
        items,
        search,
        statusFilter,
        productFilter,
    ]);

    const stats = useMemo(() => {
        const normalize = (value) =>
            String(value || "").toLowerCase();

        return {
            total: items.length,

            active: items.filter(
                (item) =>
                    normalize(item.status) === "active"
            ).length,

            negotiation: items.filter(
                (item) =>
                    normalize(item.status) ===
                    "under negotiation"
            ).length,

            expired: items.filter(
                (item) =>
                    normalize(item.status) ===
                    "expired"
            ).length,
        };
    }, [items]);

    const getInitials = (name) => {
        if (!name) return "OEM";

        const words = name
            .trim()
            .split(/\s+/)
            .filter(Boolean);

        if (words.length === 1) {
            return words[0]
                .slice(0, 2)
                .toUpperCase();
        }

        return (
            words[0][0] +
            words[1][0]
        ).toUpperCase();
    };

    const getStatusClass = (status) => {
        switch (
            String(status || "").toLowerCase()
        ) {
            case "active":
                return "oem-status-active";

            case "under negotiation":
                return "oem-status-negotiation";

            case "pending renewal":
                return "oem-status-renewal";

            case "expired":
                return "oem-status-expired";

            default:
                return "oem-status-default";
        }
    };

    if (activeRole !== ROLES.SOLUTION_ENGINEER) {
        return (
            <div className="standard-page">
                <div className="ui-card ui-card-padded">
                    <h2>Unauthorized</h2>
                    <p>
                        You do not have permission to access
                        the OEM Registry.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="oem-page">

            {/* =========================
                HEADER
            ========================= */}

            <div className="page-header">

                <div className="page-header-copy">

                    <div className="oem-eyebrow">
                        PARTNER MANAGEMENT
                    </div>

                    <h1>OEM Registry</h1>

                    <p>
                        Read-only view of OEM partners attached
                        to authorized accounts.
                    </p>

                </div>

                <div className="page-header-actions">

                    <button
                        type="button"
                        className="oem-refresh"
                        onClick={refresh}
                        disabled={loading}
                    >
                        <RefreshCw
                            size={14}
                            className={
                                loading
                                    ? "oem-spin"
                                    : ""
                            }
                        />

                        Refresh
                    </button>

                </div>

            </div>

            {/* ERROR */}

            {error && (
                <div className="oem-error">
                    {error}
                </div>
            )}

            {/* =========================
                STATS
            ========================= */}

            <div className="oem-stats">

                <div className="oem-stat">

                    <div className="oem-stat-icon oem-stat-icon-blue">
                        <Building2 size={18} />
                    </div>

                    <div className="oem-stat-content">

                        <span className="oem-stat-label">
                            Total Partners
                        </span>

                        <strong className="oem-stat-value">
                            {stats.total}
                        </strong>

                        <small className="oem-stat-description">
                            Registered OEM partners
                        </small>

                    </div>

                </div>

                <div className="oem-stat">

                    <div className="oem-stat-icon oem-stat-icon-green">
                        <CheckCircle2 size={18} />
                    </div>

                    <div className="oem-stat-content">

                        <span className="oem-stat-label">
                            Active Partners
                        </span>

                        <strong className="oem-stat-value">
                            {stats.active}
                        </strong>

                        <small className="oem-stat-description">
                            Currently active
                        </small>

                    </div>

                </div>

                <div className="oem-stat">

                    <div className="oem-stat-icon oem-stat-icon-orange">
                        <Clock3 size={18} />
                    </div>

                    <div className="oem-stat-content">

                        <span className="oem-stat-label">
                            Under Negotiation
                        </span>

                        <strong className="oem-stat-value">
                            {stats.negotiation}
                        </strong>

                        <small className="oem-stat-description">
                            In negotiation stage
                        </small>

                    </div>

                </div>

                <div className="oem-stat">

                    <div className="oem-stat-icon oem-stat-icon-red">
                        <CalendarX2 size={18} />
                    </div>

                    <div className="oem-stat-content">

                        <span className="oem-stat-label">
                            Expired
                        </span>

                        <strong className="oem-stat-value">
                            {stats.expired}
                        </strong>

                        <small className="oem-stat-description">
                            Partnerships expired
                        </small>

                    </div>

                </div>

            </div>

            {/* =========================
                REGISTRY
            ========================= */}

            <div className="ui-card oem-registry">

                {/* TOOLBAR */}

                <div className="oem-registry-toolbar">

                    <div className="ui-search oem-search">

                        <Search size={15} />

                        <input
                            value={search}
                            onChange={(e) =>
                                setSearch(
                                    e.target.value
                                )
                            }
                            placeholder="Search partners, contacts, products..."
                        />

                        {search && (
                            <button
                                type="button"
                                onClick={() =>
                                    setSearch("")
                                }
                            >
                                ×
                            </button>
                        )}

                    </div>

                    <div className="oem-filters">

                        <select
                            className="oem-filter"
                            value={statusFilter}
                            onChange={(e) =>
                                setStatusFilter(
                                    e.target.value
                                )
                            }
                        >
                            <option value="all">
                                All Statuses
                            </option>

                            <option value="active">
                                Active
                            </option>

                            <option value="under negotiation">
                                Under Negotiation
                            </option>

                            <option value="pending renewal">
                                Pending Renewal
                            </option>

                            <option value="expired">
                                Expired
                            </option>
                        </select>

                        <select
                            className="oem-filter"
                            value={productFilter}
                            onChange={(e) =>
                                setProductFilter(
                                    e.target.value
                                )
                            }
                        >
                            <option value="all">
                                All Products
                            </option>

                            {products.map((product) => (
                                <option
                                    key={product}
                                    value={product}
                                >
                                    {product}
                                </option>
                            ))}
                        </select>

                    </div>

                </div>

                {/* TABLE HEADING */}

                <div className="oem-registry-heading">

                    <div>
                        <h2>OEM Partners</h2>

                        <p>
                            {loading
                                ? "Loading..."
                                : `${filteredItems.length} partner${
                                      filteredItems.length !== 1
                                          ? "s"
                                          : ""
                                  }`}
                        </p>
                    </div>

                    {(search ||
                        statusFilter !== "all" ||
                        productFilter !== "all") && (
                        <button
                            type="button"
                            className="oem-clear"
                            onClick={() => {
                                setSearch("");
                                setStatusFilter("all");
                                setProductFilter("all");
                            }}
                        >
                            Clear filters
                        </button>
                    )}

                </div>

                {/* TABLE */}

                <div className="ui-table-wrap">

                    <table className="ui-data-table oem-table">

                        <thead>
                            <tr>
                                <th>Partner</th>
                                <th>Product</th>
                                <th>Contact</th>
                                <th>Status</th>
                            </tr>
                        </thead>

                        <tbody>

                            {loading ? (
                                <tr>
                                    <td
                                        colSpan="4"
                                        className="oem-table-loading"
                                    >
                                        <span className="oem-loading-content">
                                            <RefreshCw
                                                size={15}
                                                className="oem-spin"
                                            />
                                            Loading OEM partners...
                                        </span>
                                    </td>
                                </tr>
                            ) : filteredItems.length === 0 ? (
                                <tr>
                                    <td
                                        colSpan="4"
                                        className="oem-table-empty"
                                    >
                                        <div className="oem-empty-content">
                                            <strong>
                                                No OEM partners found
                                            </strong>

                                            <span>
                                                Try changing your
                                                search or filters.
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filteredItems.map(
                                    (item) => (
                                        <tr
                                            key={
                                                item.oem_partner_id
                                            }
                                        >

                                            {/* PARTNER */}

                                            <td>
                                                <div className="oem-partner">

                                                    <div className="oem-avatar">
                                                        {getInitials(
                                                            item.partner_name
                                                        )}
                                                    </div>

                                                    <div className="oem-partner-info">

                                                        <span className="oem-partner-name">
                                                            {
                                                                item.partner_name
                                                            }
                                                        </span>

                                                        <span className="oem-partner-subtitle">
                                                            OEM Partner
                                                        </span>

                                                    </div>

                                                </div>
                                            </td>

                                            {/* PRODUCT */}

                                            <td>
                                                <div className="oem-product">

                                                    <span className="oem-product-name">
                                                        {
                                                            item.product_name ||
                                                            "—"
                                                        }
                                                    </span>

                                                    <span className="oem-product-type">
                                                        Partner Product
                                                    </span>

                                                </div>
                                            </td>

                                            {/* CONTACT */}

                                            <td>
                                                <div className="oem-contact">

                                                    <span className="oem-contact-name">
                                                        {
                                                            item.contact_person ||
                                                            "—"
                                                        }
                                                    </span>

                                                    {item.email && (
                                                        <a
                                                            className="oem-contact-email"
                                                            href={`mailto:${item.email}`}
                                                        >
                                                            <Mail
                                                                size={11}
                                                            />

                                                            {
                                                                item.email
                                                            }
                                                        </a>
                                                    )}

                                                </div>
                                            </td>

                                            {/* STATUS */}

                                            <td>
                                                <span
                                                    className={`oem-status ${getStatusClass(
                                                        item.status
                                                    )}`}
                                                >
                                                    <span className="oem-status-dot" />

                                                    {
                                                        item.status ||
                                                        "—"
                                                    }
                                                </span>
                                            </td>

                                        </tr>
                                    )
                                )
                            )}

                        </tbody>

                    </table>

                </div>

            </div>
        </div>
    );
}