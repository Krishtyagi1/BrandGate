"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, ArrowRight, BookOpen, FileText } from "lucide-react";
import type {
  Organisation,
  User,
  Version,
  AuditEvent,
} from "../../../packages/contracts";
import type { Draft } from "../../../packages/contracts/reviews";
import { api, date, message } from "@/lib/api";
import { Badge, Empty, Loading, Notice, PageHeading } from "./ui";

export default function WorkflowDashboard({
  org,
  user,
}: {
  org: Organisation;
  user: User;
}) {
  const [data, setData] = useState<{
      versions: Version[];
      drafts: Draft[];
      events: AuditEvent[];
    } | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const abort = new AbortController();
    Promise.all([
      api<Version[]>(`/organisations/${org.id}/guidelines/versions`, {
        signal: abort.signal,
      }),
      api<Draft[]>(`/organisations/${org.id}/drafts`, { signal: abort.signal }),
      api<AuditEvent[]>(`/organisations/${org.id}/audit`, {
        signal: abort.signal,
      }),
    ])
      .then(([versions, drafts, events]) =>
        setData({ versions, drafts, events }),
      )
      .catch((e) => {
        if (!abort.signal.aborted) setError(message(e));
      });
    return () => abort.abort();
  }, [org.id]);
  if (error) return <Notice kind="error">{error}</Notice>;
  if (!data) return <Loading />;
  const active = data.versions.find((v) => v.status === "active"),
    base = `/org/${org.id}`;
  return (
    <>
      <PageHeading
        title={`Welcome, ${user.name.split(" ")[0]}.`}
        action={
          <Link className="button primary" href={`${base}/reviews/new`}>
            <Plus size={16} />
            New review
          </Link>
        }
      >
        Your content, its checks and the decisions that move it forward.
      </PageHeading>
      <div className="workflow-counts">
        {[
          ["draft", "Drafts"],
          ["needs_changes", "Needs changes"],
          ["pending_approval", "Waiting for review"],
          ["approved", "Approved"],
        ].map(([status, name]) => (
          <Link
            key={status}
            href={`${base}/${status === "pending_approval" ? "approvals" : "content"}`}
          >
            <strong>
              {data.drafts.filter((d) => d.status === status).length}
            </strong>
            <span>{name}</span>
          </Link>
        ))}
      </div>
      <div className="knowledge-line">
        <BookOpen size={18} />
        <span>
          {active
            ? `Guidelines v${active.version} · ${active.rule_count} owner-approved rules`
            : "Add and activate brand knowledge before checking content."}
        </span>
        <Link href={`${base}/brand`}>
          {active ? "View knowledge" : "Set up knowledge"}
          <ArrowRight size={14} />
        </Link>
      </div>
      <section className="panel content-list">
        <div className="section-heading dashboard-list-title">
          <h2>Recent content</h2>
          <Link href={`${base}/content`}>
            View all
            <ArrowRight size={14} />
          </Link>
        </div>
        {data.drafts.length ? (
          data.drafts.slice(0, 5).map((d) => (
            <Link
              className="content-row"
              key={d.id}
              href={`${base}/reviews/${d.id}`}
            >
              <span className="content-icon">
                <FileText size={19} />
              </span>
              <div>
                <strong>{d.title}</strong>
                <small>
                  {d.creator_name} · {d.channel}
                </small>
              </div>
              <Badge variant={d.status === "approved" ? "success" : "neutral"}>
                {d.status.replaceAll("_", " ")}
              </Badge>
              <small>{date(d.updated_at)}</small>
              <ArrowRight size={15} />
            </Link>
          ))
        ) : (
          <Empty
            title={
              active
                ? "Bring your first draft"
                : "Start with your brand knowledge"
            }
            action={
              <Link
                className="button primary"
                href={`${base}/${active ? "reviews/new" : "brand"}`}
              >
                {active ? "Create a review" : "Add brand rules"}
              </Link>
            }
          >
            {active
              ? "Write or upload content, inspect the AI payload, then check it against your approved sources."
              : "Only owner-approved, active rules become the basis of a content review."}
          </Empty>
        )}
      </section>
      <section className="panel recent-activity">
        <div className="section-heading">
          <h2>Recent activity</h2>
          <Link href={`${base}/activity`}>
            View activity
            <ArrowRight size={14} />
          </Link>
        </div>
        <div className="activity-list">
          {data.events.slice(0, 4).map((e) => (
            <div className="activity-row" key={e.id}>
              <span className="activity-icon">
                <FileText size={16} />
              </span>
              <div>
                <strong>
                  {e.action.replaceAll(".", " ").replaceAll("_", " ")}
                </strong>
                <small>{e.actor_name}</small>
              </div>
              <time dateTime={e.created_at}>{date(e.created_at)}</time>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
