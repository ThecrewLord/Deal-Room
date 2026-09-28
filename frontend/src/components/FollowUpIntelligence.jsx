import React, { useMemo, useState } from "react";
import "./FollowUpIntelligence.css";

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

const formatDueDate = (value) => {
  if (!value) return "-";

  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

export default function FollowUpIntelligence({ followUps }) {
  const [activeFilter, setActiveFilter] = useState("all");

  const items = followUps?.items || [];

  const counts = useMemo(
    () => ({
      overdue: followUps?.overdue ?? 0,
      today: followUps?.due_today ?? 0,
      upcoming: followUps?.upcoming ?? 0,
      completed: followUps?.completed ?? 0,
    }),
    [followUps]
  );

  const filteredFollowUps = useMemo(() => {
    if (activeFilter === "all") {
      return items;
    }

    return items.filter((item) => item.status === activeFilter);
  }, [items, activeFilter]);

  return (
    <section className="followup-intelligence">
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

        <button className="followup-view-all" type="button">
          View all follow-ups
          <span>→</span>
        </button>
      </div>

      <div className="followup-kpis">
        <FollowUpKpi
          type="overdue"
          icon={STATUS_CONFIG.overdue.icon}
          number={counts.overdue}
          title="Overdue"
          subtitle="Needs immediate attention"
          onClick={() => setActiveFilter("overdue")}
        />

        <FollowUpKpi
          type="today"
          icon={STATUS_CONFIG.today.icon}
          number={counts.today}
          title="Due today"
          subtitle="Action required today"
          onClick={() => setActiveFilter("today")}
        />

        <FollowUpKpi
          type="upcoming"
          icon={STATUS_CONFIG.upcoming.icon}
          number={counts.upcoming}
          title="Upcoming"
          subtitle="Next 7 days"
          onClick={() => setActiveFilter("upcoming")}
        />

        <FollowUpKpi
          type="completed"
          icon={STATUS_CONFIG.completed.icon}
          number={counts.completed}
          title="Completed"
          subtitle="Completed follow-ups"
          onClick={() => setActiveFilter("completed")}
        />
      </div>

      <div className="followup-priority">
        <div className="priority-heading">
          <div>
            <h3>Priority follow-ups</h3>
            <p>Your most important and upcoming follow-up actions.</p>
          </div>

          <div className="followup-tabs">
            <button
              type="button"
              className={activeFilter === "all" ? "active" : ""}
              onClick={() => setActiveFilter("all")}
            >
              All ({items.length})
            </button>

            <button
              type="button"
              className={activeFilter === "overdue" ? "active" : ""}
              onClick={() => setActiveFilter("overdue")}
            >
              Overdue ({counts.overdue})
            </button>

            <button
              type="button"
              className={activeFilter === "today" ? "active" : ""}
              onClick={() => setActiveFilter("today")}
            >
              Due Today ({counts.today})
            </button>

            <button
              type="button"
              className={activeFilter === "upcoming" ? "active" : ""}
              onClick={() => setActiveFilter("upcoming")}
            >
              Upcoming ({counts.upcoming})
            </button>

            <button
              type="button"
              className={activeFilter === "completed" ? "active" : ""}
              onClick={() => setActiveFilter("completed")}
            >
              Completed ({counts.completed})
            </button>
          </div>
        </div>

        {filteredFollowUps.length === 0 ? (
          <div className="followup-empty">
            <div className="followup-empty-icon">
              {activeFilter === "completed" ? "✓" : "✓"}
            </div>

            <strong>
              {activeFilter === "completed"
                ? "No completed follow-ups to display"
                : "You're all caught up"}
            </strong>

            <span>
              {activeFilter === "completed"
                ? "Completed follow-ups will appear here when available."
                : "No follow-ups require your attention right now."}
            </span>
          </div>
        ) : (
          <div className="followup-table-wrap">
            <table className="followup-table">
              <thead>
                <tr>
                  <th>OPPORTUNITY</th>
                  <th>ACTION</th>
                  <th>STAGE</th>
                  <th>DUE DATE</th>
                  <th>STATUS</th>
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
                          {item.account && <span>{item.account}</span>}
                        </div>
                      </div>
                    </td>

                    <td>
                      <div className="followup-action">
                        <strong>{item.action || "Follow up"}</strong>
                        {item.action_detail && (
                          <span>{item.action_detail}</span>
                        )}
                      </div>
                    </td>

                    <td>
                      <span
                        className={`followup-stage stage-${String(
                          item.stage || ""
                        )
                          .toLowerCase()
                          .replace(/\s+/g, "-")}`}
                      >
                        {item.stage || "-"}
                      </span>
                    </td>

                    <td>
                      <div
                        className={`followup-date followup-date-${item.status}`}
                      >
                        <strong>{item.due_label}</strong>
                        <span>{formatDueDate(item.due_date)}</span>
                      </div>
                    </td>

                    <td>
                      <span
                        className={`followup-priority-badge priority-${item.status}`}
                      >
                        <span className="priority-dot">
                          {STATUS_CONFIG[item.status]?.icon || "•"}
                        </span>

                        {STATUS_CONFIG[item.status]?.label || item.status}
                      </span>
                    </td>

                    <td>
                      <button
                        className="followup-arrow"
                        type="button"
                        aria-label="Open follow-up"
                      >
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
      type="button"
      className={`followup-kpi followup-kpi-${type}`}
      onClick={onClick}
    >
      <div className="followup-kpi-icon">{icon}</div>

      <div className="followup-kpi-content">
        <strong>{number}</strong>
        <span className="followup-kpi-title">{title}</span>
        <span className="followup-kpi-subtitle">{subtitle}</span>
      </div>

      <span className="followup-kpi-arrow">›</span>
    </button>
  );
}
