import React, { useMemo, useState } from "react";
import "./FollowUpIntelligence.css";
export default function FollowUpIntelligence({ followUps }) {
const FOLLOW_UPS = [
  {
    id: 1,
    opportunity: "Acme DevSecOps Transformation",
    account: "Acme Corp",
    action: "Confirm POC requirements",
    actionDetail: "Discuss technical scope and timeline",
    stakeholder: "Sarah Johnson",
    initials: "SJ",
    stakeholderRole: "Technical Champion",
    stage: "POC",
    dueLabel: "2 days overdue",
    dueDate: "12 Sep 2026",
    priority: "High",
    status: "overdue",
  },
  {
    id: 2,
    opportunity: "Retail CI/CD Modernization",
    account: "Global Retail Group",
    action: "Send proposal",
    actionDetail: "Share updated commercial proposal",
    stakeholder: "James Wilson",
    initials: "JW",
    stakeholderRole: "Decision Maker",
    stage: "Negotiations",
    dueLabel: "Today",
    dueDate: "14 Sep 2026",
    priority: "High",
    status: "today",
  },
  {
    id: 3,
    opportunity: "OEM Partnership Expansion",
    account: "Tech Innovations Ltd",
    action: "Schedule technical review",
    actionDetail: "Align on architecture and next steps",
    stakeholder: "Mike Chen",
    initials: "MC",
    stakeholderRole: "Technical Champion",
    stage: "RFX",
    dueLabel: "Tomorrow",
    dueDate: "15 Sep 2026",
    priority: "Medium",
    status: "upcoming",
  },
  {
    id: 4,
    opportunity: "Analytics Platform Deployment",
    account: "DataCore Systems",
    action: "Follow up on security review",
    actionDetail: "Check status of security questionnaire",
    stakeholder: "Ravi Kumar",
    initials: "RK",
    stakeholderRole: "End User",
    stage: "Qualified",
    dueLabel: "18 Sep 2026",
    dueDate: "In 4 days",
    priority: "Medium",
    status: "upcoming",
  },
  {
    id: 5,
    opportunity: "Cloud Infrastructure Upgrade",
    account: "NextGen Solutions",
    action: "Send meeting recap",
    actionDetail: "Share discussion summary and next steps",
    stakeholder: "Anita Patel",
    initials: "AP",
    stakeholderRole: "Economic Buyer",
    stage: "Lead",
    dueLabel: "20 Sep 2026",
    dueDate: "In 6 days",
    priority: "Low",
    status: "upcoming",
  },
];

const STATUS_CONFIG = {
  overdue: {
    label: "Overdue",
    icon: "!",
  },
  today: {
    label: "Due today",
    icon: "◷",
  },
  upcoming: {
    label: "Upcoming",
    icon: "▣",
  },
  completed: {
    label: "Completed",
    icon: "✓",
  },
};


  const [activeFilter, setActiveFilter] = useState("all");

  const counts = useMemo(
    () => ({
      overdue: FOLLOW_UPS.filter((x) => x.status === "overdue").length,
      today: FOLLOW_UPS.filter((x) => x.status === "today").length,
      upcoming: FOLLOW_UPS.filter((x) => x.status === "upcoming").length,
      completed: 12,
    }),
    []
  );

  const filteredFollowUps = useMemo(() => {
    if (activeFilter === "all") return FOLLOW_UPS;

    return FOLLOW_UPS.filter(
      (item) => item.status === activeFilter
    );
  }, [activeFilter]);

  return (
    <section className="followup-intelligence">
      {/* Header */}
      <div className="followup-header">
        <div className="followup-title-area">
          <div className="followup-icon">
            <span>✓</span>
          </div>

          <div>
            <h2>Follow-up Intelligence</h2>
            <p>
              Stay ahead of customer actions, deadlines, and stalled
              conversations.
            </p>
          </div>
        </div>

        <button className="followup-view-all">
          View all follow-ups
          <span>→</span>
        </button>
      </div>

      {/* KPI cards */}
      <div className="followup-kpis">
        <FollowUpKpi
          type="overdue"
          icon="!"
          number={counts.overdue}
          title="Overdue"
          subtitle="Needs immediate attention"
          onClick={() => setActiveFilter("overdue")}
        />

        <FollowUpKpi
          type="today"
          icon="◷"
          number={counts.today}
          title="Due today"
          subtitle="Action required today"
          onClick={() => setActiveFilter("today")}
        />

        <FollowUpKpi
          type="upcoming"
          icon="▣"
          number={counts.upcoming}
          title="Upcoming"
          subtitle="Next 7 days"
          onClick={() => setActiveFilter("upcoming")}
        />

        <FollowUpKpi
          type="completed"
          icon="✓"
          number={counts.completed}
          title="Completed"
          subtitle="This month"
          onClick={() => setActiveFilter("completed")}
        />
      </div>

      {/* Priority follow-ups */}
      <div className="followup-priority">
        <div className="priority-heading">
          <div>
            <h3>Priority follow-ups</h3>
            <p>Your most important and upcoming follow-up actions.</p>
          </div>

          <div className="followup-tabs">
            <button
              className={activeFilter === "all" ? "active" : ""}
              onClick={() => setActiveFilter("all")}
            >
              All ({FOLLOW_UPS.length})
            </button>

            <button
              className={activeFilter === "overdue" ? "active" : ""}
              onClick={() => setActiveFilter("overdue")}
            >
              Overdue ({counts.overdue})
            </button>

            <button
              className={activeFilter === "today" ? "active" : ""}
              onClick={() => setActiveFilter("today")}
            >
              Due Today ({counts.today})
            </button>

            <button
              className={activeFilter === "upcoming" ? "active" : ""}
              onClick={() => setActiveFilter("upcoming")}
            >
              Upcoming ({counts.upcoming})
            </button>

            <button
              className={activeFilter === "completed" ? "active" : ""}
              onClick={() => setActiveFilter("completed")}
            >
              Completed ({counts.completed})
            </button>
          </div>
        </div>

        {activeFilter === "completed" ? (
          <div className="followup-empty">
            <div className="followup-empty-icon">✓</div>
            <strong>No completed follow-ups to display</strong>
            <span>
              Completed follow-ups will appear here when available.
            </span>
          </div>
        ) : filteredFollowUps.length === 0 ? (
          <div className="followup-empty">
            <div className="followup-empty-icon">✓</div>
            <strong>You're all caught up</strong>
            <span>No follow-ups require your attention right now.</span>
          </div>
        ) : (
          <div className="followup-table-wrap">
            <table className="followup-table">
              <thead>
                <tr>
                  <th>OPPORTUNITY</th>
                  <th>ACTION</th>
                  <th>STAKEHOLDER</th>
                  <th>STAGE</th>
                  <th>DUE DATE</th>
                  <th>PRIORITY</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {filteredFollowUps.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div className="followup-opportunity">
                        <div className="opportunity-mini-icon">▣</div>

                        <div>
                          <strong>{item.opportunity}</strong>
                          <span>{item.account}</span>
                        </div>
                      </div>
                    </td>

                    <td>
                      <div className="followup-action">
                        <strong>{item.action}</strong>
                        <span>{item.actionDetail}</span>
                      </div>
                    </td>

                    <td>
                      <div className="followup-stakeholder">
                        <div className="stakeholder-avatar">
                          {item.initials}
                        </div>

                        <div>
                          <strong>{item.stakeholder}</strong>
                          <span>{item.stakeholderRole}</span>
                        </div>
                      </div>
                    </td>

                    <td>
                      <span
                        className={`followup-stage stage-${item.stage
                          .toLowerCase()
                          .replace(/\s+/g, "-")}`}
                      >
                        {item.stage}
                      </span>
                    </td>

                    <td>
                      <div
                        className={`followup-date followup-date-${item.status}`}
                      >
                        <strong>{item.dueLabel}</strong>
                        <span>{item.dueDate}</span>
                      </div>
                    </td>

                    <td>
                      <span
                        className={`followup-priority-badge priority-${item.priority.toLowerCase()}`}
                      >
                        <span className="priority-dot">
                          {item.priority === "High"
                            ? "!"
                            : item.priority === "Medium"
                            ? "✓"
                            : "✓"}
                        </span>

                        {item.priority}
                      </span>
                    </td>

                    <td>
                      <button className="followup-arrow" aria-label="Open">
                        →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function FollowUpKpi({
  type,
  icon,
  number,
  title,
  subtitle,
  onClick,
}) {
  return (
    <button
      className={`followup-kpi followup-kpi-${type}`}
      onClick={onClick}
    >
      <div className="followup-kpi-icon">
        {icon}
      </div>

      <div className="followup-kpi-content">
        <strong>{number}</strong>
        <span className="followup-kpi-title">{title}</span>
        <span className="followup-kpi-subtitle">{subtitle}</span>
      </div>

      <span className="followup-kpi-arrow">›</span>
    </button>
  );
}
