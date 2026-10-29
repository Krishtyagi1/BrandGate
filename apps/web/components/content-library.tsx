"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, FileText, ChevronRight } from "lucide-react";
import type { Organisation } from "../../../packages/contracts";
import type {
  ApprovalRequest,
  Draft,
} from "../../../packages/contracts/reviews";
import { api, date, message } from "@/lib/api";
import { Badge, Empty, Loading, Notice, PageHeading } from "./ui";

export default function ContentLibrary({
  org,
  approvals = false,
  userId,
}: {
  org: Organisation;
  approvals?: boolean;
  userId?: string;
}) {
  const [items, setItems] = useState<(Draft | ApprovalRequest)[] | null>(null),
    [error, setError] = useState(""),
    [search, setSearch] = useState(""),
    [filter, setFilter] = useState("all"),
    [queue, setQueue] = useState(approvals ? "assigned" : "all"),
    [requests, setRequests] = useState<ApprovalRequest[]>([]);
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("queue") === "assigned")
      setQueue("assigned");
    Promise.all([
      api<Draft[]>(`/organisations/${org.id}/drafts`),
      api<ApprovalRequest[]>(`/organisations/${org.id}/approvals`),
    ])
      .then(([drafts, approvals]) => {
        setItems(drafts);
        setRequests(approvals);
      })
      .catch((e) => setError(message(e)));
  }, [org.id, approvals]);
  return (
    <>
      <PageHeading
        title="Tracking"
        action={
          <Link className="button primary" href={`/org/${org.id}/reviews/new`}>
            <Plus size={16} />
            New review
          </Link>
        }
      >
        Find saved content, follow its status and review approvals assigned to
        you.
      </PageHeading>
      {error && <Notice kind="error">{error}</Notice>}
      {org.role !== "creator" && (
        <p>
          <Link className="button secondary" href={`/org/${org.id}/insights`}>
            Recurring issues & guideline gaps
          </Link>
        </p>
      )}
      <div className="library-filters">
        <label>
          <span className="sr-only">Content queue</span>
          <select
            value={queue}
            onChange={(e) => {
              setQueue(e.target.value);
              setFilter("all");
            }}
          >
            <option value="all">All content</option>
            <option value="assigned">Assigned approvals</option>
          </select>
        </label>
        <label>
          <span className="sr-only">Search content</span>
          <input
            placeholder="Search content…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <label>
          <span className="sr-only">Status</span>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            {[
              "all",
              ...(queue === "assigned"
                ? [
                    "pending",
                    "approved",
                    "needs_changes",
                    "rejected",
                    "superseded",
                  ]
                : [
                    "draft",
                    "pending_approval",
                    "approved",
                    "needs_changes",
                    "rejected",
                  ]),
            ].map((s) => (
              <option key={s} value={s}>
                {s.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!items ? (
        <Loading />
      ) : (
        <section className="panel content-list">
          {(queue === "assigned"
            ? requests.filter((r) => !userId || r.reviewer_id === userId)
            : items
          )
            .filter(
              (i) =>
                (i.title || "").toLowerCase().includes(search.toLowerCase()) &&
                (filter === "all" || i.status === filter),
            )
            .map((i) => (
              <Link
                className="content-row"
                key={i.id}
                href={`/org/${org.id}/reviews/${"draft_id" in i ? i.draft_id : i.id}`}
              >
                <span className="content-icon">
                  <FileText size={20} />
                </span>
                <div>
                  <strong>{i.title}</strong>
                  <small>
                    {i.creator_name}
                    {"reviewer_name" in i ? ` → ${i.reviewer_name}` : ""}
                  </small>
                </div>
                <Badge
                  variant={i.status === "approved" ? "success" : "neutral"}
                >
                  {i.status.replaceAll("_", " ")}
                </Badge>
                <small>
                  {date("updated_at" in i ? i.updated_at : i.created_at)}
                </small>
                <ChevronRight size={16} />
              </Link>
            ))}
          {!(
            queue === "assigned"
              ? requests.filter((r) => !userId || r.reviewer_id === userId)
              : items
          ).filter(
            (i) =>
              (i.title || "").toLowerCase().includes(search.toLowerCase()) &&
              (filter === "all" || i.status === filter),
          ).length && (
            <Empty
              title={
                queue === "assigned"
                  ? "No assigned approvals match"
                  : "No content matches"
              }
              action={
                <Link
                  className="button primary"
                  href={`/org/${org.id}/reviews/new`}
                >
                  Create a review
                </Link>
              }
            >
              {queue === "assigned"
                ? "Creators submit checked revisions to a separate authorised reviewer."
                : "Write or upload content, then check it against your approved brand knowledge."}
            </Empty>
          )}
        </section>
      )}
    </>
  );
}
