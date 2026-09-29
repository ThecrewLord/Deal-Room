import { useEffect, useState } from "react";
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
  const negotiationsBlocked =
    isClosed || !isNegotiationsReached || isDeliveryTeam;
  const collaborationBlocked = isDeliveryTeam;

  const [rfx, setRfx] = useState({ drive_link: "" });
  const [rfxEditing, setRfxEditing] = useState(false);
  const [neg, setNeg] = useState({});
  const [negotiationEditing, setNegotiationEditing] = useState(false);
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
          description={
            isClosed
              ? "This opportunity is closed. RFX context is read-only."
              : rfxBlocked
                ? "RFX becomes available when the opportunity reaches the RFX stage."
                : "Drive link is captured for POC documentation. Deal Room does not verify Drive permissions."
          }
          icon={FileText}
        >
          <div style={{ display: "flex", gap: 8 }}>
            <input
              style={{ flex: 1 }}
              value={rfx.drive_link || ""}
              placeholder="Google Drive link"
              disabled={rfxBlocked || !rfxEditing}
              onChange={(e) =>
                setRfx({
                  ...rfx,
                  drive_link: e.target.value,
                })
              }
            />

            {!rfxEditing && !rfxBlocked ? (
              <Button
                onClick={() => {
                  setError("");
                  setSuccess("");
                  setRfxEditing(true);
                }}
              >
                Edit
              </Button>
            ) : (
              <Button
                onClick={saveRfx}
                disabled={rfxBlocked}
              >
                {rfxBlocked ? "Locked" : "Save"}
              </Button>
            )}
          </div>
        </SectionCard>
      </div>

      <div style={negotiationsBlocked ? blockedStyle : undefined}>
        <SectionCard
          title="Negotiations"
          description={
            isClosed
              ? "This opportunity is closed. Negotiations context is read-only."
              : negotiationsBlocked
                ? isDeliveryTeam
                  ? "Negotiations are not available to the Delivery Team."
                  : "Negotiations becomes available when the opportunity reaches the Negotiations stage."
                : "NDA/MSA/SOW are optional. NDA may be suggested."
          }
          icon={Handshake}
        >
          <textarea
            placeholder="Negotiation notes"
            value={neg.notes || ""}
            disabled={negotiationsBlocked || !negotiationEditing}
            onChange={(e) =>
              setNeg({
                ...neg,
                notes: e.target.value,
              })
            }
          />

          <div
            style={{
              display: "flex",
              gap: 8,
              marginTop: 8,
            }}
          >
            <input
              placeholder="NDA link"
              value={neg.nda_link || ""}
              disabled={negotiationsBlocked || !negotiationEditing}
              onChange={(e) =>
                setNeg({
                  ...neg,
                  nda_link: e.target.value,
                })
              }
            />

            <input
              placeholder="MSA link"
              value={neg.msa_link || ""}
              disabled={negotiationsBlocked || !negotiationEditing}
              onChange={(e) =>
                setNeg({
                  ...neg,
                  msa_link: e.target.value,
                })
              }
            />

            <input
              placeholder="SOW link"
              value={neg.sow_link || ""}
              disabled={negotiationsBlocked || !negotiationEditing}
              onChange={(e) =>
                setNeg({
                  ...neg,
                  sow_link: e.target.value,
                })
              }
            />

            {!negotiationEditing && !negotiationsBlocked ? (
              <Button
                onClick={() => {
                  setError("");
                  setSuccess("");
                  setNegotiationEditing(true);
                }}
              >
                Edit
              </Button>
            ) : (
              <Button
                onClick={saveNeg}
                disabled={negotiationsBlocked}
              >
                {negotiationsBlocked ? "Locked" : "Save"}
              </Button>
            )}
          </div>
        </SectionCard>
      </div>

      <div style={collaborationBlocked ? blockedStyle : undefined}>
        <SectionCard
          title="Activities"
          description={
            collaborationBlocked
              ? "Activities are not available to the Delivery Team."
              : "Business interactions are separate from Audit Log."
          }
          icon={Activity}
        >
          <div style={{ display: "flex", gap: 8 }}>
            <select
              value={activity.activity_type}
              disabled={collaborationBlocked}
              onChange={(e) =>
                setActivity({
                  ...activity,
                  activity_type: e.target.value,
                })
              }
              style={{ minWidth: 130, padding: "8px" }}
            >
              <option value="note">Note</option>
              <option value="call">Call</option>
              <option value="email">Email</option>
              <option value="meeting">Meeting</option>
              <option value="demo">Demo</option>
              <option value="other">Other</option>
            </select>

            <input
              style={{ flex: 1 }}
              placeholder="Activity summary"
              value={activity.summary}
              disabled={collaborationBlocked}
              onChange={(e) =>
                setActivity({
                  ...activity,
                  summary: e.target.value,
                })
              }
            />

            <Button
              onClick={addA}
              disabled={
                collaborationBlocked || !activity.summary.trim()
              }
            >
              {collaborationBlocked ? "Locked" : "Add"}
            </Button>
          </div>

          {acts.length ? (
            acts.map((a) => (
              <div
                key={a.activity_id}
                style={{
                  padding: "12px",
                  marginTop: "10px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  display: "grid",
                  gap: "6px",
                }}
              >
                <div>
                  <strong>
                    {String(a.activity_type || "note")
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (c) => c.toUpperCase())}
                  </strong>
                </div>

                <div style={{ overflowWrap: "anywhere" }}>
                  {a.summary || "No description provided."}
                </div>

                <small style={{ color: "#6b7280" }}>
                  {a.created_at
                    ? new Date(a.created_at).toLocaleString()
                    : "Date not available"}
                </small>
              </div>
            ))
          ) : (
            <EmptyState message="No activities yet." />
          )}
        </SectionCard>
      </div>

      <SectionCard
        title="Follow-ups"
        description={
          collaborationBlocked
            ? "Follow-ups are view-only for the Delivery Team."
            : "Open, completed and overdue follow-ups."
        }
        icon={CalendarCheck}
      >
        <div
          style={{
            display: "flex",
            gap: 8,
            opacity: collaborationBlocked ? 0.6 : 1,
          }}
        >
          <input
            style={{ flex: 1 }}
            placeholder="Follow-up"
            value={fu.description}
            disabled={collaborationBlocked}
            onChange={(e) =>
              setFu({
                ...fu,
                description: e.target.value,
              })
            }
          />

          <input
            type="date"
            value={fu.due_date}
            disabled={collaborationBlocked}
            onChange={(e) =>
              setFu({
                ...fu,
                due_date: e.target.value,
              })
            }
          />

          <Button
            onClick={addF}
            disabled={
              collaborationBlocked ||
              !fu.description.trim() ||
              !fu.due_date
            }
          >
            {collaborationBlocked ? "Locked" : "Add"}
          </Button>
        </div>

        {collaborationBlocked && (
          <small
            style={{
              display: "block",
              marginTop: "8px",
              color: "#6b7280",
            }}
          >
            You can view follow-ups, but you cannot create or complete them.
          </small>
        )}

        {fus.length ? (
          fus.map((f) => {
            const isCompleted =
              String(f.status || "").toLowerCase() === "completed";

            return (
              <div
                key={f.follow_up_id}
                style={{
                  padding: "12px",
                  marginTop: "10px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <div style={{ display: "grid", gap: "4px" }}>
                  <div>
                    <strong>{f.status || "Open"}</strong>
                  </div>

                  <div>{f.description}</div>

                  <small style={{ color: "#6b7280" }}>
                    Owner: {f.owner_name || `#${f.owner_id}`}
                  </small>

                  <small style={{ color: "#6b7280" }}>
                    Created by: {f.creator_name || `#${f.created_by}`}
                  </small>

                  <small style={{ color: "#6b7280" }}>
                    Due: {f.due_date || "Date not available"}
                  </small>

                  {isCompleted && (
                    <small style={{ color: "#6b7280" }}>
                      Completed:{" "}
                      {f.completed_at
                        ? new Date(f.completed_at).toLocaleString()
                        : "Date not available"}
                    </small>
                  )}
                </div>

                {!isCompleted && (
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
          <EmptyState message="No follow-ups yet." />
        )}
      </SectionCard>
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
