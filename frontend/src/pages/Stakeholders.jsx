import { useEffect, useState } from "react";
import {
    Users,
    RefreshCw,
    Building2,
    BriefcaseBusiness,
    Mail,
} from "lucide-react";

import { getStakeholders } from "../api/stakeholderApi";
import { useAuth } from "../context/AuthContext";

import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import SearchInput from "../components/ui/SearchInput";
import EmptyState from "../components/ui/EmptyState";
import StatusBadge from "../components/ui/StatusBadge";

export default function Stakeholders() {
    const { activeRole } = useAuth();

    const [rows, setRows] = useState([]);
    const [q, setQ] = useState("");
    const [error, setError] = useState("");

    const load = async () => {
        try {
            const data = await getStakeholders();
            setRows(data);
            setError("");
        } catch (e) {
            setError(
                e?.response?.data?.message ||
                "Unable to load stakeholders."
            );
        }
    };

    useEffect(() => {
        load();
    }, [activeRole]);

    const filteredRows = rows.filter((x) =>
        [
            x.name,
            x.opportunity_name,
            x.job_title,
            x.company,
            x.email,
            ...(x.tags || []),
        ].some((value) =>
            String(value || "")
                .toLowerCase()
                .includes(q.toLowerCase())
        )
    );

    return (
        <div
            className="standard-page"
            style={{
                background:
                    "linear-gradient(180deg, #f8f9ff 0%, #ffffff 38%)",
                minHeight: "100%",
            }}
        >
            <PageHeader
                title="Stakeholders"
                description="Opportunity stakeholders and their V2 decision tags."
                actions={
                    <button
                        onClick={load}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 7,
                            background: "#ffffff",
                            border: "1px solid #e2e5f0",
                            borderRadius: 9,
                            padding: "8px 13px",
                            boxShadow:
                                "0 2px 8px rgba(79,70,229,0.05)",
                        }}
                    >
                        <RefreshCw size={14} />
                        Refresh
                    </button>
                }
            />

            {error && (
                <div className="standard-error">
                    {error}
                </div>
            )}

            <Card
                padding={false}
                style={{
                    overflow: "hidden",
                    border: "1px solid #e6e8f2",
                    boxShadow:
                        "0 8px 30px rgba(79,70,229,0.06)",
                    borderRadius: 16,
                }}
            >
                {/* Search */}
                <div
                    style={{
                        padding: "18px 22px",
                        background:
                            "linear-gradient(90deg, #fafaff, #f8fbff)",
                        borderBottom:
                            "1px solid #eaecf4",
                    }}
                >
                    <SearchInput
                        value={q}
                        onChange={setQ}
                        placeholder="Search stakeholders, opportunities, accounts..."
                    />
                </div>

                {/* Column header */}
                {filteredRows.length > 0 && (
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns:
                                "minmax(300px, 1.4fr) minmax(280px, 1fr) minmax(190px, 0.7fr)",
                            gap: 24,
                            padding: "11px 22px",
                            background: "#f7f7fc",
                            borderBottom:
                                "1px solid #e9eaf2",
                            color: "#7b8194",
                            fontSize: 10,
                            fontWeight: 700,
                            letterSpacing: "0.08em",
                            textTransform: "uppercase",
                        }}
                    >
                        <span>Stakeholder</span>
                        <span>Opportunity</span>
                        <span style={{ textAlign: "right" }}>
                            Role & Influence
                        </span>
                    </div>
                )}

                {/* Rows */}
                {filteredRows.length ? (
                    filteredRows.map((x, index) => {
                        const tags = (x.tags || []).filter(
                            (tag) =>
                                !(
                                    tag === "Decision Maker" &&
                                    x.is_decision_maker
                                )
                        );

                        const initials = (x.name || "?")
                            .trim()
                            .split(/\s+/)
                            .slice(0, 2)
                            .map((word) =>
                                word.charAt(0).toUpperCase()
                            )
                            .join("");

                        const avatarColors = [
                            {
                                bg: "#eeeaff",
                                text: "#6657c8",
                                border: "#ddd5ff",
                            },
                            {
                                bg: "#e9f5ff",
                                text: "#3478b8",
                                border: "#d2eaff",
                            },
                            {
                                bg: "#eaf8f1",
                                text: "#37805d",
                                border: "#d3efdf",
                            },
                            {
                                bg: "#fff3e8",
                                text: "#b96d32",
                                border: "#ffe1c5",
                            },
                            {
                                bg: "#fceef5",
                                text: "#a84f78",
                                border: "#f7d6e5",
                            },
                        ];

                        const avatar =
                            avatarColors[
                                index % avatarColors.length
                            ];

                        return (
                            <div
                                key={x.stakeholder_id}
                                style={{
                                    display: "grid",
                                    gridTemplateColumns:
                                        "minmax(300px, 1.4fr) minmax(280px, 1fr) minmax(190px, 0.7fr)",
                                    alignItems: "center",
                                    gap: 24,
                                    padding: "17px 22px",
                                    borderBottom:
                                        "1px solid #edf0f5",
                                    transition:
                                        "all 0.18s ease",
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background =
                                        "#fafaff";
                                    e.currentTarget.style.boxShadow =
                                        "inset 3px 0 0 #a99bea";
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background =
                                        "transparent";
                                    e.currentTarget.style.boxShadow =
                                        "none";
                                }}
                            >
                                {/* Stakeholder */}
                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: 13,
                                        minWidth: 0,
                                    }}
                                >
                                    <div
                                        style={{
                                            width: 44,
                                            height: 44,
                                            minWidth: 44,
                                            borderRadius: 13,
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "center",
                                            background:
                                                avatar.bg,
                                            color:
                                                avatar.text,
                                            border:
                                                `1px solid ${avatar.border}`,
                                            fontSize: 13,
                                            fontWeight: 750,
                                            boxShadow:
                                                "0 3px 10px rgba(80,70,130,0.06)",
                                        }}
                                    >
                                        {initials}
                                    </div>

                                    <div
                                        style={{
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
                                                marginBottom: 5,
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
                                                {x.name}
                                            </strong>

                                            {x.is_decision_maker && (
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
                                                            "#eaf8f0",
                                                        color:
                                                            "#32805a",
                                                        border:
                                                            "1px solid #cdebd9",
                                                        fontSize: 9,
                                                        fontWeight: 700,
                                                    }}
                                                >
                                                    ● Decision Maker
                                                </span>
                                            )}
                                        </div>

                                        <div
                                            style={{
                                                display:
                                                    "flex",
                                                alignItems:
                                                    "center",
                                                gap: 5,
                                                color:
                                                    "#8a90a3",
                                                fontSize: 11,
                                            }}
                                        >
                                            <Mail
                                                size={12}
                                            />

                                            <span
                                                style={{
                                                    overflow:
                                                        "hidden",
                                                    textOverflow:
                                                        "ellipsis",
                                                    whiteSpace:
                                                        "nowrap",
                                                }}
                                            >
                                                {x.email ||
                                                    "No email provided"}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Opportunity */}
                                <div
                                    style={{
                                        minWidth: 0,
                                    }}
                                >
                                    <div
                                        style={{
                                            display:
                                                "flex",
                                            alignItems:
                                                "center",
                                            gap: 9,
                                            marginBottom: 6,
                                        }}
                                    >
                                        <div
                                            style={{
                                                width: 30,
                                                height: 30,
                                                borderRadius: 9,
                                                display:
                                                    "flex",
                                                alignItems:
                                                    "center",
                                                justifyContent:
                                                    "center",
                                                background:
                                                    "#eeedff",
                                                color:
                                                    "#6b5fc7",
                                                border:
                                                    "1px solid #dfdcff",
                                            }}
                                        >
                                            <BriefcaseBusiness
                                                size={14}
                                            />
                                        </div>

                                        <span
                                            style={{
                                                fontSize: 13,
                                                fontWeight: 650,
                                                color:
                                                    "#30344a",
                                                overflow:
                                                    "hidden",
                                                textOverflow:
                                                    "ellipsis",
                                                whiteSpace:
                                                    "nowrap",
                                            }}
                                        >
                                            {x.opportunity_name ||
                                                "Unknown Opportunity"}
                                        </span>
                                    </div>

                                    <div
                                        style={{
                                            display:
                                                "flex",
                                            alignItems:
                                                "center",
                                            gap: 6,
                                            marginLeft: 39,
                                        }}
                                    >
                                        <Building2
                                            size={12}
                                            color="#9ba1b2"
                                        />

                                        <span
                                            style={{
                                                fontSize: 11,
                                                color:
                                                    "#858b9e",
                                                overflow:
                                                    "hidden",
                                                textOverflow:
                                                    "ellipsis",
                                                whiteSpace:
                                                    "nowrap",
                                            }}
                                        >
                                            {x.company ||
                                                "No account"}
                                        </span>
                                    </div>
                                </div>

                                {/* Role / Tags */}
                                <div
                                    style={{
                                        display:
                                            "flex",
                                        flexDirection:
                                            "column",
                                        alignItems:
                                            "flex-end",
                                        gap: 7,
                                    }}
                                >
                                    <span
                                        style={{
                                            padding:
                                                "5px 10px",
                                            borderRadius: 8,
                                            background:
                                                "#fff5ea",
                                            color:
                                                "#a96832",
                                            border:
                                                "1px solid #f7dfc5",
                                            fontSize: 11,
                                            fontWeight: 650,
                                        }}
                                    >
                                        {x.job_title ||
                                            "No job title"}
                                    </span>

                                    {tags.length > 0 && (
                                        <div
                                            style={{
                                                display:
                                                    "flex",
                                                flexWrap:
                                                    "wrap",
                                                justifyContent:
                                                    "flex-end",
                                                gap: 5,
                                            }}
                                        >
                                            {tags.map(
                                                (tag) => {
                                                    const tagStyle =
                                                        tag ===
                                                        "Economic Buyer"
                                                            ? {
                                                                  bg: "#fff1f7",
                                                                  text: "#a54d76",
                                                                  border: "#f5d4e3",
                                                              }
                                                            : tag ===
                                                              "Technical Champion"
                                                            ? {
                                                                  bg: "#edf6ff",
                                                                  text: "#3975ad",
                                                                  border: "#d4e9fb",
                                                              }
                                                            : tag ===
                                                              "Blocker"
                                                            ? {
                                                                  bg: "#fff2f0",
                                                                  text: "#b45d55",
                                                                  border: "#f4d7d2",
                                                              }
                                                            : tag ===
                                                              "End User"
                                                            ? {
                                                                  bg: "#eef9f3",
                                                                  text: "#43805e",
                                                                  border: "#d5edde",
                                                              }
                                                            : {
                                                                  bg: "#f3f1ff",
                                                                  text: "#675db0",
                                                                  border: "#e0dcfa",
                                                              };

                                                    return (
                                                        <span
                                                            key={
                                                                tag
                                                            }
                                                            style={{
                                                                padding:
                                                                    "4px 8px",
                                                                borderRadius:
                                                                    999,
                                                                background:
                                                                    tagStyle.bg,
                                                                color:
                                                                    tagStyle.text,
                                                                border:
                                                                    `1px solid ${tagStyle.border}`,
                                                                fontSize:
                                                                    10,
                                                                fontWeight:
                                                                    650,
                                                                whiteSpace:
                                                                    "nowrap",
                                                            }}
                                                        >
                                                            {
                                                                tag
                                                            }
                                                        </span>
                                                    );
                                                }
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <EmptyState message="No stakeholders found." />
                )}
            </Card>
        </div>
    );
}