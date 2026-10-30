"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, date, message } from "@/lib/api";
import { Badge, Loading, Notice } from "./ui";

interface Finding {
  id: string;
  category: string;
  severity: string;
  status: string;
  dismissed: boolean;
  quote: string;
  reason: string;
}
interface DocumentResult {
  id: string;
  title: string;
  creator_name: string;
  channel: string;
  workflow_status: string;
  review_state: string;
  coverage_incomplete: boolean;
  open_flags: number;
  high_flags: number;
  findings: Finding[];
}
interface DashboardData {
  scope: string;
  refreshed_at: string;
  days: number;
  notice: string;
  summary: Record<string, number>;
  breakdowns: Record<
    "category" | "severity" | "status",
    { label: string; count: number }[]
  >;
  activity: {
    day: string;
    total: number;
    completed: number;
    incomplete: number;
    failed: number;
    in_progress: number;
  }[];
  documents: DocumentResult[];
}
const label = (value: string) => value.replaceAll("_", " ");
const incomplete = (d: DocumentResult) =>
  d.coverage_incomplete ||
  [
    "incomplete",
    "failed",
    "cancelled",
    "interrupted",
    "running",
    "queued",
  ].includes(d.review_state);
const metrics = [
  ["documents", "All documents"],
  ["checked_documents", "Completed latest checks"],
  ["flagged_documents", "Documents with open flags"],
  ["open_flags", "Open flags"],
  ["high_flags", "High-severity flags"],
  ["incomplete_documents", "Incomplete or unfinished checks"],
  ["stale_documents", "Outdated reviews"],
  ["pending_approvals", "Pending human approvals"],
  ["unchecked_documents", "Not checked yet"],
  ["dismissed_flags", "Dismissed observations"],
] as const;

export default function ReviewDashboard({ orgId }: { orgId: string }) {
  const [days, setDays] = useState(30),
    [refresh, setRefresh] = useState(0);
  const [data, setData] = useState<DashboardData | null>(null),
    [error, setError] = useState("");
  const [metric, setMetric] = useState("attention"),
    [search, setSearch] = useState("");
  const [category, setCategory] = useState("all"),
    [severity, setSeverity] = useState("all"),
    [status, setStatus] = useState("all");
  const [visible, setVisible] = useState(20);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setData(null);
    api<DashboardData>(`/organisations/${orgId}/dashboard?days=${days}`, {
      signal: controller.signal,
    })
      .then(setData)
      .catch((e) => {
        if (!controller.signal.aborted) setError(message(e));
      });
    return () => controller.abort();
  }, [orgId, days, refresh]);
  useEffect(() => {
    setVisible(20);
  }, [metric, search, category, severity, status]);
  function reset() {
    setMetric("attention");
    setSearch("");
    setCategory("all");
    setSeverity("all");
    setStatus("all");
  }
  function metricMatches(d: DocumentResult) {
    switch (metric) {
      case "documents":
        return true;
      case "checked_documents":
        return d.review_state === "completed";
      case "flagged_documents":
      case "open_flags":
        return d.open_flags > 0;
      case "high_flags":
        return d.high_flags > 0;
      case "incomplete_documents":
        return incomplete(d);
      case "stale_documents":
        return d.review_state === "stale";
      case "pending_approvals":
        return d.workflow_status === "pending_approval";
      case "unchecked_documents":
        return d.review_state === "unchecked";
      case "dismissed_flags":
        return d.findings.some((f) => f.dismissed);
      default:
        return (
          d.open_flags > 0 ||
          incomplete(d) ||
          ["stale", "unchecked"].includes(d.review_state) ||
          d.workflow_status === "pending_approval"
        );
    }
  }
  const filtered =
    data?.documents.filter((d) => {
      const matchText = `${d.title} ${d.creator_name} ${d.channel}`
        .toLowerCase()
        .includes(search.toLowerCase());
      const matchFinding =
        (category === "all" && severity === "all" && status === "all") ||
        d.findings.some(
          (f) =>
            (metric === "dismissed_flags" ? f.dismissed : !f.dismissed) &&
            (metric !== "high_flags" || f.severity === "high") &&
            (category === "all" || f.category === category) &&
            (severity === "all" || f.severity === severity) &&
            (status === "all" || f.status === status),
        );
      return metricMatches(d) && matchText && matchFinding;
    }) || [];
  return (
    <section
      className="review-dashboard"
      aria-labelledby="review-overview-title"
    >
      <div className="section-heading dashboard-heading">
        <div>
          <h2 id="review-overview-title">Review overview</h2>
          <p>
            {data?.scope === "your_documents"
              ? "Your documents and their latest review results."
              : "Current documents, open flags and work awaiting attention."}
          </p>
        </div>
        <button
          className="button secondary compact"
          onClick={() => setRefresh((n) => n + 1)}
        >
          Refresh dashboard
        </button>
      </div>
      {error && (
        <Notice kind="error">{error} Use Refresh dashboard to retry.</Notice>
      )}
      {!data && !error && <Loading />}
      {data && (
        <>
          <small className="dashboard-refreshed">
            {data.scope === "your_documents"
              ? "Your documents only"
              : "Organisation overview"}{" "}
            · Refreshed {date(data.refreshed_at)}
          </small>
          <div className="dashboard-metrics">
            {metrics.map(([key, title]) => (
              <button
                key={key}
                aria-pressed={metric === key}
                onClick={() => setMetric(key)}
              >
                <strong>{data.summary[key]}</strong>
                <span>{title}</span>
              </button>
            ))}
          </div>
          <p className="muted dashboard-denominator">{data.notice}</p>
          <div className="dashboard-breakdowns">
            {(["category", "severity", "status"] as const).map((dimension) => (
              <section className="panel" key={dimension}>
                <h3>Open flags by {dimension}</h3>
                {!data.breakdowns[dimension].length ? (
                  <p className="muted">No current open flags.</p>
                ) : (
                  data.breakdowns[dimension].map((row) => (
                    <button
                      key={row.label}
                      className="dashboard-bar"
                      onClick={() => {
                        setMetric("open_flags");
                        if (dimension === "category") setCategory(row.label);
                        if (dimension === "severity") setSeverity(row.label);
                        if (dimension === "status") setStatus(row.label);
                      }}
                    >
                      <span>{label(row.label)}</span>
                      <strong>{row.count}</strong>
                      <span className="dashboard-bar-track" aria-hidden="true">
                        <span
                          style={{
                            width: `${(row.count / Math.max(1, data.summary.open_flags)) * 100}%`,
                          }}
                        />
                      </span>
                    </button>
                  ))
                )}
              </section>
            ))}
          </div>
          <section className="panel dashboard-activity">
            <div className="section-heading">
              <h3>Review activity · last {days} days</h3>
              <label>
                Review activity period
                <select
                  aria-label="Review activity period"
                  value={days}
                  onChange={(e) => setDays(Number(e.target.value))}
                >
                  {[7, 30, 90].map((n) => (
                    <option key={n} value={n}>
                      Last {n} days
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <p className="muted">
              Review runs started in this period, including rechecks. Days use
              UTC; current totals above cover all documents.
            </p>
            {!data.activity.length ? (
              <p>No reviews started in this period.</p>
            ) : (
              <details>
                <summary>
                  {data.activity.reduce((n, d) => n + d.total, 0)} review runs ·
                  View daily results
                </summary>
                <div
                  className="dashboard-table"
                  tabIndex={0}
                  role="region"
                  aria-label="Daily review activity"
                >
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Day</th>
                        <th scope="col">Complete</th>
                        <th scope="col">Incomplete</th>
                        <th scope="col">Failed / stopped</th>
                        <th scope="col">In progress</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.activity.map((day) => (
                        <tr key={day.day}>
                          <th scope="row">{day.day}</th>
                          <td>{day.completed}</td>
                          <td>{day.incomplete}</td>
                          <td>{day.failed}</td>
                          <td>{day.in_progress}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            )}
          </section>
          <section className="panel dashboard-attention">
            <div className="section-heading">
              <h3>
                {metric === "attention"
                  ? "Needs attention"
                  : "Matching documents"}{" "}
                ({filtered.length})
              </h3>
              <button className="button ghost compact" onClick={reset}>
                Reset dashboard filters
              </button>
            </div>
            <p className="muted">
              {metric === "attention"
                ? "Open flags, incomplete or outdated checks, unchecked content and pending approvals."
                : metrics.find(([key]) => key === metric)?.[1]}{" "}
              · Filters below apply to this list. The saved-work list below has
              its own filters.
            </p>
            <div className="dashboard-filters">
              <label>
                Search dashboard documents
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Title, creator or channel"
                />
              </label>
              {(
                [
                  ["category", category, setCategory],
                  ["severity", severity, setSeverity],
                  ["status", status, setStatus],
                ] as const
              ).map(([dimension, value, change]) => (
                <label key={dimension}>
                  Flag {dimension}
                  <select
                    aria-label={`Flag ${dimension}`}
                    value={value}
                    onChange={(e) => change(e.target.value)}
                  >
                    <option value="all">
                      All{" "}
                      {dimension === "category"
                        ? "categories"
                        : dimension === "severity"
                          ? "severities"
                          : "statuses"}
                    </option>
                    {[
                      ...new Set(
                        data.documents.flatMap((d) =>
                          d.findings.map((f) => f[dimension]),
                        ),
                      ),
                    ]
                      .sort()
                      .map((v) => (
                        <option key={v} value={v}>
                          {label(v)}
                        </option>
                      ))}
                  </select>
                </label>
              ))}
            </div>
            {!filtered.length && <p>No documents match these filters.</p>}
            {filtered.slice(0, visible).map((d) => (
              <article className="dashboard-document" key={d.id}>
                <div>
                  <Link href={`/org/${orgId}/reviews/${d.id}`}>
                    <strong>{d.title}</strong>
                  </Link>
                  <p className="muted">
                    {d.creator_name} · {label(d.channel)}
                  </p>
                  {d.findings
                    .filter((f) => !f.dismissed)
                    .slice(0, 2)
                    .map((f) => (
                      <p key={f.id}>
                        {label(f.severity)} · {f.reason}
                      </p>
                    ))}
                </div>
                <div className="dashboard-document-state">
                  <Badge>{label(d.review_state)}</Badge>
                  <Badge>{label(d.workflow_status)}</Badge>
                  <span>
                    {d.open_flags} open flags
                    {d.high_flags ? ` · ${d.high_flags} high severity` : ""}
                  </span>
                  {d.coverage_incomplete && (
                    <span>Some checks lack complete coverage</span>
                  )}
                  {["completed", "incomplete"].includes(d.review_state) && (
                    <Link href={`/org/${orgId}/reviews/${d.id}#document-chat`}>
                      Ask why it was flagged
                    </Link>
                  )}
                </div>
              </article>
            ))}
            {filtered.length > visible && (
              <button
                className="button secondary compact"
                onClick={() => setVisible((n) => n + 20)}
              >
                Show more documents ({filtered.length - visible} remaining)
              </button>
            )}
          </section>
        </>
      )}
    </section>
  );
}
