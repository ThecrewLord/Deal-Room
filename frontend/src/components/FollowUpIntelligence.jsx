import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getDashboardFollowUps } from "../api/dashboardApi";
import LoadingState from "./ui/LoadingState";
import ErrorState from "./ui/ErrorState";
import "./FollowUpIntelligence.css";

const PAGE_SIZE = 10;
const FILTERS = [
  { key: "all", label: "All" },
  { key: "overdue", label: "Overdue" },
  { key: "today", label: "Due Today" },
  { key: "upcoming", label: "Upcoming" },
  { key: "completed", label: "Completed" },
];
const STATUS_CONFIG = {
  overdue: { label: "Overdue", icon: "!" },
  today: { label: "Due today", icon: "◷" },
  upcoming: { label: "Upcoming", icon: "▣" },
  completed: { label: "Completed", icon: "✓" },
};

const formatDueDate = (value) => {
  if (!value) return "-";
  // ISO date-only values are parsed as local calendar dates to avoid UTC day shifts.
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
};

export default function FollowUpIntelligence({ followUps }) {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [pageData, setPageData] = useState({ items: [], total: 0, total_pages: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const counts = useMemo(() => ({
    overdue: followUps?.overdue ?? 0,
    today: followUps?.due_today ?? 0,
    upcoming: followUps?.upcoming ?? 0,
    completed: followUps?.completed ?? 0,
  }), [followUps]);

  const load = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getDashboardFollowUps({ filter: activeFilter, page, pageSize: PAGE_SIZE });
      setPageData(data || { items: [], total: 0, total_pages: 0 });
    } catch (err) {
      setError(err?.response?.data?.message || "Unable to load follow-ups.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [activeFilter, page]);

  const selectFilter = (filter) => {
    setActiveFilter(filter);
    setPage(1);
  };
  const items = pageData.items || [];
  const filterCounts = {
    all: followUps?.total ?? pageData.total ?? 0,
    overdue: counts.overdue,
    today: counts.today,
    upcoming: counts.upcoming,
    completed: counts.completed,
  };
  const pageNumbers = Math.max(1, Number(pageData.total_pages || 0));

  return (
    <section className="followup-intelligence">
      <div className="followup-header">
        <div className="followup-title-area">
          <div className="followup-icon"><span>✓</span></div>
          <div>
            <h2>Follow-up Intelligence</h2>
            <p>Stay ahead of customer actions, deadlines, and stalled conversations.</p>
          </div>
        </div>
        <button className="followup-view-all" type="button" onClick={() => selectFilter("all")}>
          View all follow-ups <span>→</span>
        </button>
      </div>

      <div className="followup-priority">
        <div className="priority-heading">
          <div>
            <h3>Priority follow-ups</h3>
            <p>Your customer actions and upcoming follow-up commitments.</p>
          </div>
          <div className="followup-tabs" role="tablist" aria-label="Follow-up filters">
            {FILTERS.map((filter) => (
              <button
                key={filter.key}
                type="button"
                role="tab"
                aria-selected={activeFilter === filter.key}
                className={activeFilter === filter.key ? "active" : ""}
                onClick={() => selectFilter(filter.key)}
              >
                {filter.label} ({filterCounts[filter.key] ?? 0})
              </button>
            ))}
          </div>
        </div>

        {error ? <ErrorState message={error} onRetry={load} /> : loading ? <LoadingState message="Loading follow-ups…" /> : items.length === 0 ? (
          <div className="followup-empty">
            <div className="followup-empty-icon">✓</div>
            <strong>{activeFilter === "completed" ? "No completed follow-ups to display" : "No follow-ups found"}</strong>
            <span>{activeFilter === "completed" ? "Completed follow-ups will appear here when available." : "Try another filter or check back when new follow-ups are created."}</span>
          </div>
        ) : (
          <>
            <div className="followup-table-wrap">
              <table className="followup-table">
                <thead><tr><th>OPPORTUNITY</th><th>ACTION</th><th>STAGE</th><th>DUE DATE</th><th>STATUS</th><th /></tr></thead>
                <tbody>
                  {items.map((item) => {
                    const status = STATUS_CONFIG[item.status];
                    const openOpportunity = () => {
                      if (item.opportunity_id != null) navigate(`/opportunity/${item.opportunity_id}`);
                    };
                    return (
                      <tr key={item.id}>
                        <td>
                          <div className="followup-opportunity">
                            <div className="opportunity-mini-icon">▣</div>
                            <div>
                              {item.opportunity_id != null ? (
                                <button className="followup-opportunity-link" type="button" onClick={openOpportunity}>
                                  {item.opportunity || `Opportunity #${item.opportunity_id}`}
                                </button>
                              ) : <strong>{item.opportunity || "Opportunity unavailable"}</strong>}
                              {item.account && <span>{item.account}</span>}
                            </div>
                          </div>
                        </td>
                        <td><div className="followup-action"><strong>{item.action || "Follow up"}</strong>{item.action_detail && <span>{item.action_detail}</span>}</div></td>
                        <td><span className={`followup-stage stage-${String(item.stage || "").toLowerCase().replace(/\s+/g, "-")}`}>{item.stage || "-"}</span></td>
                        <td><div className={`followup-date followup-date-${item.status}`}><strong>{item.due_label || "-"}</strong><span>{formatDueDate(item.due_date)}</span></div></td>
                        <td><span className={`followup-priority-badge priority-${item.status}`}><span className="priority-dot">{status?.icon || "•"}</span>{status?.label || item.status}</span></td>
                        <td><button className="followup-arrow" type="button" aria-label={`Open ${item.opportunity || "opportunity"}`} disabled={item.opportunity_id == null} onClick={openOpportunity}>→</button></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {pageNumbers > 1 && (
              <div className="followup-pagination">
                <span>Page {page} of {pageNumbers} · {pageData.total} follow-ups</span>
                <div>
                  <button type="button" disabled={page <= 1 || loading} onClick={() => setPage((current) => Math.max(1, current - 1))}>Previous</button>
                  <button type="button" disabled={page >= pageNumbers || loading} onClick={() => setPage((current) => Math.min(pageNumbers, current + 1))}>Next</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
