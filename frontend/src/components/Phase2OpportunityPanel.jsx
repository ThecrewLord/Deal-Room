import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  Activity,
  CalendarCheck,
  FileText,
  Handshake,
  Briefcase,
} from "lucide-react";

import {
  getRfx,
  updateRfx,
  getNegotiations,
  updateNegotiations,
  getActivities,
  addActivity,
  getFollowUps,
  addFollowUp,
  completeFollowUp,
  getDeliveryProject,
} from "../api/phase2Api";

import SectionCard from "./ui/SectionCard";
import Button from "./ui/Button";
import EmptyState from "./ui/EmptyState";
import { ROLES } from "../auth/roles";

export default function Phase2OpportunityPanel({
  opportunity,
  activeRole,
  onRefresh,
}) {
  const { user: currentUser } = useAuth();
  const id = opportunity.opportunity_id;

  const stage = String(
    opportunity.lifecycle_stage ||
      opportunity.stage_name ||
      opportunity.stage ||
      opportunity.current_stage ||
      ""
  ).trim();

  const normalizedStage = stage.toLowerCase();

  const isRfxReached = ["rfx", "poc", "negotiations", "delivery"].includes(
    normalizedStage
  );

  const isNegotiationsReached = ["negotiations", "delivery"].includes(
    normalizedStage
  );

  const isDeliveryReached = normalizedStage === "delivery";
  const isClosed = opportunity.operational_status === "Closed";

  const isDeliveryTeam =
    activeRole === ROLES.DELIVERY_MANAGER ||
    activeRole === ROLES.DEVOPS_ENGINEER ||
    activeRole === ROLES.DATA_ANALYST;

  const rfxBlocked = isClosed || !isRfxReached;
  const leadershipRfxReadOnly = activeRole === ROLES.LEADERSHIP;

  const negotiationsBlocked =
    isClosed || !isNegotiationsReached || isDeliveryTeam;
  const collaborationBlocked = isDeliveryTeam;

  const [rfx, setRfx] = useState({ drive_link: "" });
  const [rfxEditing, setRfxEditing] = useState(false);
  const [rfxCollapsed, setRfxCollapsed] = useState(rfxBlocked);
  const [neg, setNeg] = useState({});
  const [negotiationEditing, setNegotiationEditing] = useState(false);
  const [negotiationsCollapsed, setNegotiationsCollapsed] = useState(negotiationsBlocked);
  const [acts, setActs] = useState([]);
  const [fus, setFus] = useState([]);
  const [delivery, setDelivery] = useState(null);

  const [activity, setActivity] = useState({
    activity_type: "note",
    summary: "",
  });
  const [fu, setFu] = useState({
    description: "",
    due_date: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const load = async () => {
    const [r, n, ac, fuRows, d] = await Promise.all([
      getRfx(id).catch(() => null),
      getNegotiations(id).catch(() => null),
      getActivities(id).catch(() => null),
      getFollowUps(id).catch(() => null),
      isDeliveryReached
        ? getDeliveryProject(id).catch(() => null)
        : Promise.resolve(null),
    ]);

    if (r !== null) {
      const rfxContext = r || {};
      setRfx(rfxContext);
      setRfxEditing(!rfxContext.rfx_context_id);
    }
    if (n !== null) {
      const negotiation = n || {};
      setNeg(negotiation);
      setNegotiationEditing(!negotiation.negotiation_context_id);
    }
    if (ac !== null) setActs(ac || []);
    if (fuRows !== null) setFus(fuRows || []);
    setDelivery(d);
  };

  useEffect(() => {
    load();
  }, [id]);

  const saveRfx = async () => {
    if (rfxBlocked) return;

    setError("");
    setSuccess("");

    try {
      await updateRfx(id, {
        drive_link: rfx.drive_link,
        row_version: rfx.row_version,
      });

      await load();
      setRfxEditing(false);
      onRefresh?.();
      setSuccess("RFX context saved successfully.");

      window.setTimeout(() => {
        setSuccess("");
      }, 3000);
    } catch (e) {
      setError(
        e?.response?.data?.message || "Unable to save RFX context."
      );
    }
  };

  const saveNeg = async () => {
    if (negotiationsBlocked) return;

    setError("");
    setSuccess("");

    try {
      await updateNegotiations(id, {
        nda_suggested: Boolean(neg.nda_suggested),
        nda_link: neg.nda_link || "",
        msa_link: neg.msa_link || "",
        sow_link: neg.sow_link || "",
        notes: neg.notes || "",
        row_version: neg.row_version,
      });

      await load();
      onRefresh?.();
      setNegotiationEditing(false);
      setSuccess("Negotiation context saved successfully.");

      window.setTimeout(() => {
        setSuccess("");
      }, 3000);
    } catch (e) {
      setError(
        e?.response?.data?.message || "Unable to save Negotiations."
      );
    }
  };

  const addA = async () => {
    if (collaborationBlocked || !activity.summary.trim()) return;

    try {
      await addActivity(id, {
        activity_type: activity.activity_type,
        summary: activity.summary,
      });

      setActivity({
        activity_type: "note",
        summary: "",
      });
      await load();
      onRefresh?.();
    } catch (e) {
      setError(
        e?.response?.data?.message || "Unable to add activity."
      );
    }
  };

  const addF = async () => {
    if (
      collaborationBlocked ||
      !fu.description.trim() ||
      !fu.due_date
    ) {
      return;
    }

    try {
      await addFollowUp(id, fu);

      setFu({
        description: "",
        due_date: "",
      });

      await load();
      onRefresh?.();
    } catch (e) {
      setError(
        e?.response?.data?.message || "Unable to add follow-up."
      );
    }
  };

  const completeF = async (followUpId) => {
    if (collaborationBlocked) return;

    setError("");
    setSuccess("");

    try {
      await completeFollowUp(followUpId);
      await load();
      onRefresh?.();
      setSuccess("Follow-up completed successfully.");

      window.setTimeout(() => {
        setSuccess("");
      }, 3000);
    } catch (e) {
      setError(
        e?.response?.data?.message || "Unable to complete follow-up."
      );
    }
  };

  const blockedStyle = {
    opacity: 0.5,
    filter: "grayscale(0.8)",
  };

  return (
    <div style={{ display: "grid", gap: 16 }}>
      {error && <div className="standard-error">{error}</div>}
      {success && (
        <div
          style={{
            padding: "10px 12px",
            borderRadius: 6,
            border: "1px solid #b7dfc5",
            background: "#eefaf2",
            color: "#176b35",
            fontWeight: 600,
          }}
        >
          ✓ {success}
        </div>
      )}

      <div style={rfxBlocked ? blockedStyle : undefined}>
  <SectionCard
    title="RFX Context"
    collapsible={rfxBlocked}
    collapsed={rfxCollapsed}
    onToggle={() => setRfxCollapsed(!rfxCollapsed)}
    description={
      isClosed
        ? "This opportunity is closed. RFX context is read-only."
        : leadershipRfxReadOnly
          ? "RFX context is view-only for Leadership."
          : rfxBlocked
            ? "RFX becomes available when the opportunity reaches the RFX stage."
            : "Capture the key RFX documentation for this opportunity."
    }
    icon={FileText}
  >
    <div
      style={{
        display: "grid",
        gap: "16px",
      }}
    >
      {/* RFX header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          padding: "14px 16px",
          borderRadius: "12px",
          background: "linear-gradient(135deg, #f5f7ff 0%, #eef2ff 100%)",
          border: "1px solid #dfe4ff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              display: "grid",
              placeItems: "center",
              background: "#e0e7ff",
              color: "#4f46e5",
            }}
          >
            <FileText size={18} />
          </div>

          <div>
            <strong
              style={{
                display: "block",
                fontSize: "14px",
              }}
            >
              RFX Documentation
            </strong>

            <small style={{ color: "#64748b" }}>
              Store the reference document used during the RFX stage.
            </small>
          </div>
        </div>

        {rfx.drive_link ? (
          <span
            style={{
              padding: "5px 9px",
              borderRadius: "999px",
              background: "#dcfce7",
              color: "#166534",
              fontSize: "11px",
              fontWeight: 700,
            }}
          >
            Document Added
          </span>
        ) : (
          <span
            style={{
              padding: "5px 9px",
              borderRadius: "999px",
              background: "#fef3c7",
              color: "#92400e",
              fontSize: "11px",
              fontWeight: 700,
            }}
          >
            Not Added
          </span>
        )}
      </div>

      {/* Drive link */}
      <div
        style={{
          padding: "16px",
          borderRadius: "12px",
          border: "1px solid #e5e7eb",
          background: "#ffffff",
        }}
      >
        <label
          style={{
            display: "block",
            marginBottom: "8px",
            fontSize: "12px",
            fontWeight: 700,
            color: "#475569",
          }}
        >
          RFX Document / Google Drive Link
        </label>

        <div
          style={{
            display: "flex",
            gap: "10px",
            alignItems: "center",
          }}
        >
          <input
            style={{
              flex: 1,
              minWidth: 0,
              padding: "11px 13px",
              borderRadius: "9px",
              border: "1px solid #dbe1ea",
              background: rfxBlocked || leadershipRfxReadOnly
                ? "#f8fafc"
                : "#ffffff",
            }}
            value={rfx.drive_link || ""}
            placeholder="https://drive.google.com/..."
            disabled={
              rfxBlocked ||
              leadershipRfxReadOnly ||
              isDeliveryTeam ||
              !rfxEditing
            }
            onChange={(e) =>
              setRfx({
                ...rfx,
                drive_link: e.target.value,
              })
            }
          />

          {rfx.drive_link && (
            <Button
              variant="secondary"
              onClick={() =>
                window.open(
                  rfx.drive_link,
                  "_blank",
                  "noopener,noreferrer"
                )
              }
            >
              Open
            </Button>
          )}
        </div>

        <small
          style={{
            display: "block",
            marginTop: "8px",
            color: "#94a3b8",
          }}
        >
          Deal Room stores the link but does not verify Google Drive permissions.
        </small>
      </div>

      {/* Actions */}
      {!isDeliveryTeam && !leadershipRfxReadOnly && !rfxBlocked && (
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "8px",
          }}
        >
          {!rfxEditing ? (
            <Button
              onClick={() => {
                setError("");
                setSuccess("");
                setRfxEditing(true);
              }}
            >
              Edit RFX
            </Button>
          ) : (
            <Button
              onClick={saveRfx}
              disabled={rfxBlocked}
            >
              Save RFX
            </Button>
          )}
        </div>
      )}
    </div>
  </SectionCard>
</div>

            <div style={negotiationsBlocked ? blockedStyle : undefined}>
        <SectionCard
          title="Negotiations"
          collapsible={negotiationsBlocked}
          collapsed={negotiationsCollapsed}
          onToggle={() =>
            setNegotiationsCollapsed(!negotiationsCollapsed)
          }
          description={
            isClosed
              ? "This opportunity is closed. Negotiation context is read-only."
              : negotiationsBlocked
                ? isDeliveryTeam
                  ? "Negotiations are not available to the Delivery Team."
                  : "Negotiations becomes available when the opportunity reaches the Negotiations stage."
                : "Track commercial documents and important negotiation details."
          }
          icon={Handshake}
        >
          <div style={{ display: "grid", gap: "16px" }}>

            {/* Status */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "14px 16px",
                borderRadius: "12px",
                background: "#f8fafc",
                border: "1px solid #e2e8f0",
              }}
            >
              <div>
                <strong
                  style={{
                    display: "block",
                    fontSize: "14px",
                  }}
                >
                  Negotiation Status
                </strong>

                <small style={{ color: "#64748b" }}>
                  Commercial discussion and documentation
                </small>
              </div>

              <span
                style={{
                  padding: "6px 11px",
                  borderRadius: "999px",
                  fontSize: "11px",
                  fontWeight: 700,
                  background: neg.negotiation_context_id
                    ? "#dcfce7"
                    : "#fef3c7",
                  color: neg.negotiation_context_id
                    ? "#166534"
                    : "#92400e",
                }}
              >
                {neg.negotiation_context_id
                  ? "IN PROGRESS"
                  : "NOT STARTED"}
              </span>
            </div>

            {/* Negotiation notes */}
            <div>
              <label
                style={{
                  display: "block",
                  marginBottom: "8px",
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#475569",
                }}
              >
                Negotiation Notes
              </label>

              <textarea
                style={{
                  width: "100%",
                  minHeight: "100px",
                  boxSizing: "border-box",
                  resize: "vertical",
                  padding: "11px 13px",
                  borderRadius: "9px",
                  border: "1px solid #dbe1ea",
                }}
                placeholder="Add pricing discussions, customer concerns, blockers or important negotiation details..."
                value={neg.notes || ""}
                disabled={
                  negotiationsBlocked ||
                  !negotiationEditing
                }
                onChange={(e) =>
                  setNeg({
                    ...neg,
                    notes: e.target.value,
                  })
                }
              />
            </div>

            {/* Documents */}
            <div
              style={{
                padding: "16px",
                borderRadius: "12px",
                border: "1px solid #e5e7eb",
              }}
            >
              <div style={{ marginBottom: "14px" }}>
                <strong
                  style={{
                    display: "block",
                    fontSize: "14px",
                  }}
                >
                  Commercial Documents
                </strong>

                <small style={{ color: "#64748b" }}>
                  NDA, MSA and SOW references
                </small>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(3, minmax(0, 1fr))",
                  gap: "12px",
                }}
              >
                {[
                  {
                    key: "nda_link",
                    code: "NDA",
                    title: "Non-Disclosure Agreement",
                    description:
                      "Protects confidential information shared with the customer.",
                    placeholder: "Paste NDA document link",
                    badgeBg: "#e8f1ff",
                    badgeColor: "#2563eb",
                  },
                  {
                    key: "msa_link",
                    code: "MSA",
                    title: "Master Services Agreement",
                    description:
                      "Defines the overall terms of the business relationship.",
                    placeholder: "Paste MSA document link",
                    badgeBg: "#e9f9f0",
                    badgeColor: "#15803d",
                  },
                  {
                    key: "sow_link",
                    code: "SOW",
                    title: "Statement of Work",
                    description:
                      "Defines the agreed scope, deliverables and responsibilities.",
                    placeholder: "Paste SOW document link",
                    badgeBg: "#fff4df",
                    badgeColor: "#b45309",
                  },
                ].map((doc) => (
                  <div
                    key={doc.key}
                    style={{
                      border: "1px solid var(--border)",
                      borderRadius: "10px",
                      padding: "14px",
                      background: "var(--surface)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "9px",
                        marginBottom: "8px",
                      }}
                    >
                      <span
                        style={{
                          padding: "4px 8px",
                          borderRadius: "6px",
                          background: doc.badgeBg,
                          color: doc.badgeColor,
                          fontSize: "11px",
                          fontWeight: 800,
                          letterSpacing: "0.4px",
                        }}
                      >
                        {doc.code}
                      </span>

                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: "13px",
                        }}
                      >
                        {doc.title}
                      </span>
                    </div>

                    <div
                      style={{
                        fontSize: "12px",
                        lineHeight: 1.5,
                        color: "var(--muted)",
                        marginBottom: "12px",
                      }}
                    >
                      {doc.description}
                    </div>

                    <input
                      style={{
                        width: "100%",
                        boxSizing: "border-box",
                      }}
                      placeholder={doc.placeholder}
                      value={neg[doc.key] || ""}
                      disabled={
                        negotiationsBlocked ||
                        !negotiationEditing
                      }
                      onChange={(e) =>
                        setNeg({
                          ...neg,
                          [doc.key]: e.target.value,
                        })
                      }
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* NDA suggestion */}
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "13px",
              }}
            >
              <input
                type="checkbox"
                checked={Boolean(neg.nda_suggested)}
                disabled={
                  negotiationsBlocked ||
                  !negotiationEditing
                }
                onChange={(e) =>
                  setNeg({
                    ...neg,
                    nda_suggested: e.target.checked,
                  })
                }
              />

              <span>
                NDA suggested for this opportunity
              </span>
            </label>

            {/* Actions */}
            {!isDeliveryTeam &&
              !negotiationsBlocked && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "8px",
                  }}
                >
                  {!negotiationEditing ? (
                    <Button
                      onClick={() => {
                        setError("");
                        setSuccess("");
                        setNegotiationEditing(true);
                      }}
                    >
                      Edit Negotiations
                    </Button>
                  ) : (
                    <Button
                      onClick={saveNeg}
                      disabled={negotiationsBlocked}
                    >
                      Save Negotiations
                    </Button>
                  )}
                </div>
              )}
          </div>
        </SectionCard>
      </div>

      <div style={collaborationBlocked ? blockedStyle : undefined}>
        <SectionCard
          title="Follow-ups"
          description={
            collaborationBlocked
              ? "Follow-ups are view-only for the Delivery Team."
              : "Track customer actions, internal tasks and important next steps."
          }
          icon={CalendarCheck}
        >
          {/* Add Follow-up */}
          <div
            style={{
              padding: "16px",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              background: "var(--surface)",
              opacity: collaborationBlocked ? 0.65 : 1,
            }}
          >
            <div style={{ marginBottom: "12px" }}>
              <strong
                style={{
                  display: "block",
                  fontSize: "14px",
                  marginBottom: "4px",
                }}
              >
                Add a Follow-up
              </strong>

              <small style={{ color: "var(--muted)" }}>
                Record the next action that needs to be completed.
              </small>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 180px auto",
                gap: "10px",
                alignItems: "end",
              }}
            >
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "12px",
                    fontWeight: 600,
                    marginBottom: "6px",
                    color: "var(--muted)",
                  }}
                >
                  Next Action
                </label>

                <textarea
                  style={{
                    width: "100%",
                    minHeight: "90px",
                    boxSizing: "border-box",
                    resize: "vertical",
                    padding: "11px 13px",
                    borderRadius: "9px",
                    border: "1px solid #dbe1ea",
                    background: "#ffffff",
                    fontSize: "13px",
                    lineHeight: 1.5,
                    outline: "none",
                  }}
                  placeholder="Describe the action that needs to be completed...\n\nExample: Send the revised pricing proposal to the customer and schedule a review call."
                  value={fu.description}
                  disabled={collaborationBlocked}
                  onChange={(e) =>
                    setFu({
                      ...fu,
                      description: e.target.value,
                    })
                  }
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "12px",
                    fontWeight: 600,
                    marginBottom: "6px",
                    color: "var(--muted)",
                  }}
                >
                  Due Date
                </label>

                <input
                  type="date"
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                  }}
                  value={fu.due_date}
                  disabled={collaborationBlocked}
                  onChange={(e) =>
                    setFu({
                      ...fu,
                      due_date: e.target.value,
                    })
                  }
                />
              </div>

              <Button
                onClick={addF}
                disabled={
                  collaborationBlocked ||
                  !fu.description.trim() ||
                  !fu.due_date
                }
              >
                {collaborationBlocked ? "Locked" : "Add Follow-up"}
              </Button>
            </div>

            {collaborationBlocked && (
              <small
                style={{
                  display: "block",
                  marginTop: "10px",
                  color: "var(--muted)",
                }}
              >
                You can view follow-ups, but you cannot create or complete them.
              </small>
            )}
          </div>

          {/* Follow-up list */}
          <div
            style={{
              display: "grid",
              gap: "10px",
              marginTop: "16px",
            }}
          >
            {fus.length ? (
              fus.map((f) => {
                const isCompleted =
                  String(f.status || "").toLowerCase() === "completed";

                const isOverdue =
                  !isCompleted &&
                  f.due_date &&
                  new Date(f.due_date) < new Date();

                return (
                  <div
                    key={f.follow_up_id}
                    style={{
                      padding: "15px",
                      border: "1px solid var(--border)",
                      borderRadius: "10px",
                      background: "var(--surface)",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "16px",
                      opacity: isCompleted ? 0.65 : 1,
                    }}
                  >
                    <div
                      style={{
                        display: "grid",
                        gap: "6px",
                        minWidth: 0,
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          flexWrap: "wrap",
                        }}
                      >
                        <span
                          style={{
                            padding: "4px 8px",
                            borderRadius: "6px",
                            fontSize: "11px",
                            fontWeight: 700,
                            background: isCompleted
                              ? "#ecfdf3"
                              : isOverdue
                                ? "#fef2f2"
                                : "#eff6ff",
                            color: isCompleted
                              ? "#15803d"
                              : isOverdue
                                ? "#dc2626"
                                : "#2563eb",
                          }}
                        >
                          {isCompleted
                            ? "COMPLETED"
                            : isOverdue
                              ? "OVERDUE"
                              : "OPEN"}
                        </span>

                        <strong style={{ fontSize: "14px" }}>
                          {f.description}
                        </strong>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          gap: "14px",
                          flexWrap: "wrap",
                          fontSize: "12px",
                          color: "var(--muted)",
                        }}
                      >
                        <span>
                          📅 Due: {f.due_date || "Date not available"}
                        </span>

                        <span>
                          Created by:{" "}
                          {f.creator_name || `#${f.created_by}`}
                        </span>
                      </div>

                      {isCompleted && (
                        <small style={{ color: "var(--muted)" }}>
                          Completed:{" "}
                          {f.completed_at
                            ? new Date(f.completed_at).toLocaleString()
                            : "Date not available"}
                        </small>
                      )}
                    </div>

                    {!isCompleted &&
                      Number(currentUser?.user_id) ===
                        Number(f.created_by) && (
                        <Button
                          onClick={() => completeF(f.follow_up_id)}
                          disabled={collaborationBlocked}
                        >
                          {collaborationBlocked ? "Locked" : "Complete"}
                        </Button>
                      )}
                  </div>
                );
              })
            ) : (
              <EmptyState message="No follow-ups yet. Add the next action above." />
            )}
          </div>
        </SectionCard>
      </div>

      {delivery && (
        <SectionCard
          title="Delivery Project"
          description="Separate aggregate created from Closed Won."
          icon={Briefcase}
        >
          <p>
            Status: <strong>{delivery.status}</strong>
          </p>
          <p>Delivery Manager: #{delivery.manager_id}</p>
          <p>Members: {delivery.members.length}</p>
        </SectionCard>
      )}
    </div>
  );
}
