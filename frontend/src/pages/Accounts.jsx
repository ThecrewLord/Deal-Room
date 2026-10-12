import { useEffect, useMemo, useState } from "react";
import {
    Building2,
    RefreshCw,
    Plus,
    Archive,
    Ban,
    ShieldCheck,
    RotateCcw,
} from "lucide-react";

import {
    getAccounts,
    createAccount,
    archiveAccount,
    banAccount,
    unbanAccount,
    restoreAccount,
} from "../api/accountApi";

import { useAuth } from "../context/AuthContext";
import { ROLES } from "../auth/roles";

import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import SearchInput from "../components/ui/SearchInput";
import EmptyState from "../components/ui/EmptyState";

export default function Accounts() {
    const { activeRole } = useAuth();

    const [rows, setRows] = useState([]);
    const [q, setQ] = useState("");
    const [form, setForm] = useState({
        account_name: "",
        industry: "",
        website: "",
    });
    const [show, setShow] = useState(false);
    const [error, setError] = useState("");

    const load = async () => {
        try {
            setError("");
            setRows(await getAccounts());
        } catch (e) {
            setError(
                e?.response?.data?.message ||
                    "Unable to load accounts."
            );
        }
    };

    useEffect(() => {
        load();
    }, [activeRole]);

    const visible = useMemo(
        () =>
            rows.filter((a) =>
                [
                    a.account_name,
                    a.industry,
                    a.city,
                    a.state,
                    a.country,
                ].some((v) =>
                    String(v || "")
                        .toLowerCase()
                        .includes(q.toLowerCase())
                )
            ),
        [rows, q]
    );

    const leadership = activeRole === ROLES.LEADERSHIP;

    const submit = async (e) => {
        e.preventDefault();

        try {
            await createAccount(form);

            setForm({
                account_name: "",
                industry: "",
                website: "",
            });

            setShow(false);
            load();
        } catch (x) {
            setError(
                x?.response?.data?.message ||
                    "Unable to create account."
            );
        }
    };

    const handleArchive = async (account) => {
        if (
            !window.confirm(
                `Archive "${account.account_name}"? This will prevent it from being selected for new opportunities.`
            )
        ) {
            return;
        }

        try {
            setError("");
            await archiveAccount(account.account_id);
            await load();
        } catch (x) {
            setError(
                x?.response?.data?.message ||
                    "Archive failed"
            );
        }
    };

    const handleBan = async (account) => {
        if (
            !window.confirm(
                `Ban "${account.account_name}"? This will prevent it from being selected for new opportunities.`
            )
        ) {
            return;
        }

        try {
            setError("");
            await banAccount(account.account_id);
            await load();
        } catch (x) {
            setError(
                x?.response?.data?.message ||
                    "Ban failed"
            );
        }
    };

    const handleRestore = async (account) => {
        if (
            !window.confirm(
                `Restore "${account.account_name}" and make it Active again?`
            )
        ) {
            return;
        }

        try {
            setError("");
            await restoreAccount(account.account_id);
            await load();
        } catch (x) {
            setError(
                x?.response?.data?.message ||
                    "Restore failed"
            );
        }
    };

    const handleUnban = async (account) => {
        if (
            !window.confirm(
                `Unban "${account.account_name}" and make it Active again?`
            )
        ) {
            return;
        }

        try {
            setError("");
            await unbanAccount(account.account_id);
            await load();
        } catch (x) {
            setError(
                x?.response?.data?.message ||
                    "Unban failed"
            );
        }
    };

    const getIndustryStyle = (industry) => {
        const value = String(industry || "").toLowerCase();

        if (value.includes("health")) {
            return {
                background: "#edf8f1",
                color: "#43805e",
                border: "#d4eddd",
            };
        }

        if (value.includes("financial")) {
            return {
                background: "#eeeefe",
                color: "#625bb0",
                border: "#dcd9fa",
            };
        }

        if (value.includes("technology") || value.includes("tech")) {
            return {
                background: "#edf6ff",
                color: "#3975ad",
                border: "#d5e8f8",
            };
        }

        if (value.includes("retail")) {
            return {
                background: "#fff4e9",
                color: "#ad6d36",
                border: "#f5dfc7",
            };
        }

        if (value.includes("logistics")) {
            return {
                background: "#fff0f5",
                color: "#a65378",
                border: "#f3d6e3",
            };
        }

        if (value.includes("manufacturing")) {
            return {
                background: "#f2efff",
                color: "#6759aa",
                border: "#dfd9f8",
            };
        }

        return {
            background: "#f3f5f8",
            color: "#667085",
            border: "#e1e5eb",
        };
    };

    const getAvatarStyle = (index) => {
        const styles = [
            {
                background: "#eeeaff",
                color: "#6657c8",
                border: "#ddd5ff",
            },
            {
                background: "#e9f5ff",
                color: "#3478b8",
                border: "#d2eaff",
            },
            {
                background: "#eaf8f1",
                color: "#37805d",
                border: "#d3efdf",
            },
            {
                background: "#fff3e8",
                color: "#b96d32",
                border: "#ffe1c5",
            },
            {
                background: "#fceef5",
                color: "#a84f78",
                border: "#f7d6e5",
            },
        ];

        return styles[index % styles.length];
    };

    return (
        <div
            className="standard-page"
            style={{
                background:
                    "linear-gradient(180deg, #f8f9ff 0%, #ffffff 42%)",
                minHeight: "100%",
            }}
        >
            <PageHeader
                title="Accounts"
                description="Canonical company directory. Accounts are separate from Opportunity pipeline views."
                actions={
                    <>
                        <Button
                            variant="secondary"
                            onClick={load}
                        >
                            <RefreshCw size={14} />
                            Refresh
                        </Button>

                        <Button
                            onClick={() => setShow(!show)}
                        >
                            <Plus size={14} />
                            Create Account
                        </Button>
                    </>
                }
            />

            {error && (
                <div className="standard-error">
                    {error}
                </div>
            )}

            {/* Create Account */}
            {show && (
                <Card
                    style={{
                        marginBottom: 18,
                        borderRadius: 15,
                        border: "1px solid #e4e5f2",
                        background:
                            "linear-gradient(135deg, #faf9ff, #f7fbff)",
                        boxShadow:
                            "0 6px 24px rgba(79,70,229,0.06)",
                    }}
                >
                    <form
                        onSubmit={submit}
                        style={{
                            display: "grid",
                            gap: 12,
                        }}
                    >
                        <input
                            required
                            placeholder="Company name"
                            value={form.account_name}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    account_name:
                                        e.target.value,
                                })
                            }
                        />

                        <input
                            placeholder="Industry"
                            value={form.industry}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    industry:
                                        e.target.value,
                                })
                            }
                        />

                        <input
                            placeholder="Website (optional)"
                            value={form.website}
                            onChange={(e) =>
                                setForm({
                                    ...form,
                                    website:
                                        e.target.value,
                                })
                            }
                        />

                        <Button type="submit">
                            Save Account
                        </Button>
                    </form>
                </Card>
            )}

            <Card
                padding={false}
                style={{
                    overflow: "hidden",
                    borderRadius: 16,
                    border: "1px solid #e5e7f0",
                    boxShadow:
                        "0 8px 30px rgba(79,70,229,0.06)",
                }}
            >
                {/* Search */}
                <div
                    style={{
                        padding: "18px 20px",
                        background:
                            "linear-gradient(90deg, #fafaff, #f8fbff)",
                        borderBottom:
                            "1px solid #eaecf4",
                    }}
                >
                    <SearchInput
                        value={q}
                        onChange={setQ}
                        placeholder="Search accounts..."
                    />
                </div>

                {visible.length ? (
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns:
                                "1fr 1fr",
                            columnGap: 0,
                        }}
                    >
                        {visible.map((a, index) => {
                            const isActive =
                                a.status === "Active";
                            const isBanned =
                                a.status === "Banned";
                            const isArchived =
                                a.status === "Archived";

                            const avatar =
                                getAvatarStyle(index);

                            const industry =
                                getIndustryStyle(
                                    a.industry
                                );

                            return (
                                <div
                                    key={
                                        a.account_id
                                    }
                                    style={{
                                        display:
                                            "flex",
                                        alignItems:
                                            "center",
                                        gap: 13,
                                        minHeight: 105,
                                        padding:
                                            "17px 22px",
                                        borderBottom:
                                            "1px solid #edf0f5",
                                        borderRight:
                                            index %
                                                2 ===
                                                0
                                                ? "1px solid #edf0f5"
                                                : "none",
                                        background:
                                            isBanned
                                                ? "#fff7f7"
                                                : "transparent",
                                        transition:
                                            "all 0.18s ease",
                                        position:
                                            "relative",
                                    }}
                                    onMouseEnter={(
                                        e
                                    ) => {
                                        e.currentTarget.style.background =
                                            isBanned
                                                ? "#fff5f5"
                                                : "#fafaff";
                                    }}
                                    onMouseLeave={(
                                        e
                                    ) => {
                                        e.currentTarget.style.background =
                                            isBanned
                                                ? "#fff7f7"
                                                : "transparent";
                                    }}
                                >
                                    {/* Account icon */}
                                    <div
                                        style={{
                                            width: 46,
                                            height: 46,
                                            minWidth: 46,
                                            borderRadius:
                                                13,
                                            display:
                                                "flex",
                                            alignItems:
                                                "center",
                                            justifyContent:
                                                "center",
                                            background:
                                                isBanned
                                                    ? "#ffe7e7"
                                                    : avatar.background,
                                            color:
                                                isBanned
                                                    ? "#c65353"
                                                    : avatar.color,
                                            border: `1px solid ${
                                                isBanned
                                                    ? "#f5caca"
                                                    : avatar.border
                                            }`,
                                            boxShadow:
                                                "0 3px 10px rgba(80,70,130,0.05)",
                                        }}
                                    >
                                        <Building2
                                            size={19}
                                        />
                                    </div>

                                    {/* Account information */}
                                    <div
                                        style={{
                                            flex: 1,
                                            minWidth: 0,
                                        }}
                                    >
                                        <div
                                            style={{
                                                display:
                                                    "flex",
                                                alignItems:
                                                    "center",
                                                gap: 8,
                                                marginBottom: 6,
                                            }}
                                        >
                                            <strong
                                                style={{
                                                    fontSize: 14,
                                                    fontWeight: 650,
                                                    color:
                                                        "#202438",
                                                    overflow:
                                                        "hidden",
                                                    textOverflow:
                                                        "ellipsis",
                                                    whiteSpace:
                                                        "nowrap",
                                                }}
                                            >
                                                {
                                                    a.account_name
                                                }
                                            </strong>
                                        </div>

                                        <div
                                            style={{
                                                display:
                                                    "flex",
                                                alignItems:
                                                    "center",
                                                gap: 7,
                                                flexWrap:
                                                    "wrap",
                                            }}
                                        >
                                            <span
                                                style={{
                                                    padding:
                                                        "4px 8px",
                                                    borderRadius:
                                                        7,
                                                    background:
                                                        industry.background,
                                                    color:
                                                        industry.color,
                                                    border:
                                                        `1px solid ${industry.border}`,
                                                    fontSize:
                                                        10,
                                                    fontWeight:
                                                        650,
                                                }}
                                            >
                                                {a.industry ||
                                                    "Industry not specified"}
                                            </span>

                                            <span
                                                style={{
                                                    fontSize:
                                                        11,
                                                    color:
                                                        "#8a90a3",
                                                }}
                                            >
                                                Status
                                            </span>

                                            <span
                                                style={{
                                                    display:
                                                        "inline-flex",
                                                    alignItems:
                                                        "center",
                                                    gap: 4,
                                                    padding:
                                                        "3px 7px",
                                                    borderRadius:
                                                        999,
                                                    background:
                                                        isActive
                                                            ? "#eaf8f0"
                                                            : isBanned
                                                            ? "#fff0f0"
                                                            : "#f1f2f5",
                                                    color:
                                                        isActive
                                                            ? "#39805b"
                                                            : isBanned
                                                            ? "#b85454"
                                                            : "#737987",
                                                    border:
                                                        `1px solid ${
                                                            isActive
                                                                ? "#d1ecdc"
                                                                : isBanned
                                                                ? "#f2d2d2"
                                                                : "#e1e3e8"
                                                        }`,
                                                    fontSize:
                                                        10,
                                                    fontWeight:
                                                        700,
                                                }}
                                            >
                                                <span>
                                                    ●
                                                </span>
                                                {a.status}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    {leadership &&
                                        isActive && (
                                            <div
                                                style={{
                                                    display:
                                                        "flex",
                                                    gap: 7,
                                                }}
                                            >
                                                <Button
                                                    size="sm"
                                                    variant="secondary"
                                                    onClick={() =>
                                                        handleArchive(
                                                            a
                                                        )
                                                    }
                                                >
                                                    <Archive
                                                        size={
                                                            13
                                                        }
                                                    />
                                                    Archive
                                                </Button>

                                                <Button
                                                    size="sm"
                                                    variant="secondary"
                                                    onClick={() =>
                                                        handleBan(
                                                            a
                                                        )
                                                    }
                                                >
                                                    <Ban
                                                        size={
                                                            13
                                                        }
                                                    />
                                                    Ban
                                                </Button>
                                            </div>
                                        )}

                                    {leadership &&
                                        isBanned && (
                                            <Button
                                                size="sm"
                                                variant="secondary"
                                                onClick={() =>
                                                    handleUnban(
                                                        a
                                                    )
                                                }
                                            >
                                                <ShieldCheck
                                                    size={
                                                        13
                                                    }
                                                />
                                                Unban
                                            </Button>
                                        )}

                                    {leadership &&
                                        isArchived && (
                                            <Button
                                                size="sm"
                                                variant="secondary"
                                                onClick={() =>
                                                    handleRestore(
                                                        a
                                                    )
                                                }
                                            >
                                                <RotateCcw
                                                    size={
                                                        13
                                                    }
                                                />
                                                Restore
                                            </Button>
                                        )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <EmptyState message="No matching accounts." />
                )}
            </Card>
        </div>
    );
}