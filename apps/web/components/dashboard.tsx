"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Check,
  FileCheck2,
  Users,
  ShieldCheck,
  Circle,
} from "lucide-react";
import type {
  Organisation,
  User,
  Version,
  Member,
  AuditEvent,
} from "../../../packages/contracts";
import { api, date, message } from "@/lib/api";
import { Badge, Loading, Notice, PageHeading } from "./ui";

export default function Dashboard({
  org,
  user,
}: {
  org: Organisation;
  user: User;
}) {
  const [data, setData] = useState<{
    versions: Version[];
    members: Member[];
    events: AuditEvent[];
  } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const abort = new AbortController();
    Promise.all([
      api<Version[]>(`/organisations/${org.id}/guidelines/versions`, {
        signal: abort.signal,
      }),
      api<Member[]>(`/organisations/${org.id}/members`, {
        signal: abort.signal,
      }),
      api<AuditEvent[]>(`/organisations/${org.id}/audit`, {
        signal: abort.signal,
      }),
    ])
      .then(([versions, members, events]) =>
        setData({ versions, members, events }),
      )
      .catch((e) => {
        if (!abort.signal.aborted) setError(message(e));
      });
    return () => abort.abort();
  }, [org.id]);
  if (error) return <Notice kind="error">{error}</Notice>;
  if (!data) return <Loading />;
  const active = data.versions.find((v) => v.status === "active");
  const base = `/org/${org.id}`;
  const team = data.members.filter((m) => m.status === "active");
  return (
    <>
      <PageHeading
        title={`Welcome, ${user.name.split(" ")[0]}.`}
        action={
          <Badge variant={active ? "success" : "neutral"}>
            {active ? "Brand knowledge active" : "Setup in progress"}
          </Badge>
        }
      >
        A clear view of your brand’s foundation.
      </PageHeading>
      <div className="dashboard-grid">
        <section className="setup-panel">
          <div className="section-heading">
            <span className="icon-tile">
              <BookOpen size={22} />
            </span>
            <Badge>Getting started</Badge>
          </div>
          <h2>
            Good content starts
            <br />
            with a shared standard.
          </h2>
          <p>
            Keep the facts, language and guidance your team can rely on in one
            place. Only knowledge approved by your owner becomes active.
          </p>
          <Link href={`${base}/brand`} className="button primary">
            {active ? "Open brand knowledge" : "Add your brand knowledge"}
            <ArrowRight size={17} />
          </Link>
          <div className="setup-checklist">
            <div>
              <span className="step-check done">
                <Check size={14} />
              </span>
              <span>
                <strong>Create your organisation</strong>
                <small>{org.name} is ready</small>
              </span>
              <Badge variant="success">Done</Badge>
            </div>
            <div>
              <span className={`step-check ${active ? "done" : ""}`}>
                {active ? <Check size={14} /> : <Circle size={13} />}
              </span>
              <span>
                <strong>Approve your brand guidelines</strong>
                <small>
                  {active
                    ? `Version ${active.version} is active`
                    : "Upload a document or add rules manually"}
                </small>
              </span>
              {active && <Badge variant="success">Done</Badge>}
            </div>
            <div>
              <span className={`step-check ${team.length > 1 ? "done" : ""}`}>
                {team.length > 1 ? <Check size={14} /> : <Circle size={13} />}
              </span>
              <span>
                <strong>Bring your team together</strong>
                <small>
                  {team.length > 1
                    ? `${team.length} active members`
                    : "Invite a creator or reviewer"}
                </small>
              </span>
              <Link href={`${base}/settings`}>
                {team.length > 1 ? "Manage" : "Invite"}
              </Link>
            </div>
          </div>
        </section>
        <div className="overview-side">
          <section className="panel knowledge-summary">
            <span className="icon-tile teal">
              <ShieldCheck size={22} />
            </span>
            <h3>Approved knowledge</h3>
            {active ? (
              <>
                <div className="version-number">Version {active.version}</div>
                <Badge variant="success">Active</Badge>
                <p>
                  {active.rule_count} owner-approved rules
                  <br />
                  Activated {date(active.activated_at!)}
                </p>
              </>
            ) : (
              <>
                <h4>No active guidelines yet</h4>
                <p>
                  Add and activate your brand rules before starting a compliance
                  review.
                </p>
              </>
            )}
            <Link href={`${base}/brand`}>
              Manage guidelines
              <ArrowRight size={15} />
            </Link>
          </section>
          <section className="panel team-summary">
            <Users size={21} />
            <div>
              <h3>Your team</h3>
              <p>
                {team.length} active {team.length === 1 ? "member" : "members"}
              </p>
            </div>
            <Link href={`${base}/settings`} aria-label="Manage team">
              <ArrowRight size={18} />
            </Link>
          </section>
        </div>
      </div>
      <section className="panel recent-activity">
        <div className="section-heading">
          <div>
            <h2>Recent activity</h2>
            <p className="muted">
              An accountable record of changes in your workspace.
            </p>
          </div>
          <Link href={`${base}/activity`}>
            View activity
            <ArrowRight size={15} />
          </Link>
        </div>
        <div className="activity-list">
          {data.events.slice(0, 4).map((event) => (
            <div className="activity-row" key={event.id}>
              <span className="activity-icon">
                <FileCheck2 size={17} />
              </span>
              <div>
                <strong>
                  {event.action.replaceAll(".", " ").replaceAll("_", " ")}
                </strong>
                <small>{event.actor_name}</small>
              </div>
              <time dateTime={event.created_at}>{date(event.created_at)}</time>
            </div>
          ))}
        </div>
      </section>
      <div className="foundation-note">
        <ShieldCheck size={17} />
        <p>
          Only an authorised human can approve content. AI reviews and the
          content approval workflow will arrive in later development phases.
        </p>
      </div>
    </>
  );
}
