"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { HttpAgent } from "@ag-ui/client";
import {
  Check,
  Copy,
  Activity,
  Play,
  Square,
  Users,
  Building2,
  ShieldCheck,
} from "lucide-react";
import type {
  AuditEvent,
  Member,
  Organisation,
} from "../../../packages/contracts";
import { api, date, message, send } from "@/lib/api";
import { Badge, Empty, Loading, Notice, PageHeading } from "./ui";
import AiSettings from "./ai-settings";

export function SettingsPage({
  org,
  onUpdated,
}: {
  org: Organisation;
  onUpdated: () => Promise<unknown>;
}) {
  const [members, setMembers] = useState<Member[] | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const owner = org.role === "owner";
  const base = `/organisations/${org.id}`;
  const load = useCallback(
    async () => setMembers(await api<Member[]>(`${base}/members`)),
    [base],
  );
  useEffect(() => {
    void load().catch((e) => setError(message(e)));
  }, [load]);
  async function action(work: () => Promise<void>) {
    setError("");
    setSuccess("");
    setBusy(true);
    try {
      await work();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function rename(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await action(async () => {
      await api(base, send("PATCH", { name: data.get("name") }));
      await onUpdated();
      setSuccess("Organisation name saved.");
    });
  }
  async function invite(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await action(async () => {
      const result = await api<{ token: string }>(
        `${base}/invites`,
        send("POST", { email: data.get("email"), role: data.get("role") }),
      );
      setToken(result.token);
      setSuccess(
        "Invitation created. Share the code with the intended teammate. It expires in 24 hours.",
      );
    });
  }
  async function update(member: Member, role: string, status: string) {
    await action(async () => {
      await api(
        `${base}/members/${member.id}`,
        send("PATCH", { role, status }),
      );
      await load();
      setSuccess("Member access updated.");
    });
  }
  return (
    <>
      <PageHeading title="Team & settings">
        Give the right people access to your brand workspace.
      </PageHeading>
      {error && <Notice kind="error">{error}</Notice>}
      {success && <Notice kind="success">{success}</Notice>}
      <AiSettings org={org} />
      <section className="panel">
        <div className="section-heading">
          <h2>
            <Building2 size={20} />
            Organisation
          </h2>
          <Badge variant="role">Your role: {org.role}</Badge>
        </div>
        <form className="inline-form" onSubmit={rename}>
          <label>
            Organisation name
            <input
              name="name"
              required
              maxLength={100}
              defaultValue={org.name}
              disabled={!owner}
            />
          </label>
          {owner && (
            <button className="button secondary" disabled={busy}>
              Save name
            </button>
          )}
        </form>
      </section>
      <section className="panel settings-section">
        <div className="section-heading">
          <div>
            <h2>
              <Users size={20} />
              Members
            </h2>
            <p className="muted">
              Creators draft content. Reviewers check it. Owners manage
              knowledge and access.
            </p>
          </div>
        </div>
        {!members ? (
          <Loading />
        ) : (
          <div className="member-list">
            {members.map((member) => (
              <div className="member-row" key={member.id}>
                <span className="avatar">{member.name[0]}</span>
                <div className="member-identity">
                  <strong>{member.name}</strong>
                  <small>{member.email}</small>
                </div>
                {owner && member.role !== "owner" ? (
                  <label className="sr-only-label">
                    <span className="sr-only">Role for {member.name}</span>
                    <select
                      aria-label={`Role for ${member.name}`}
                      value={member.role}
                      onChange={(e) =>
                        void update(member, e.target.value, member.status)
                      }
                      disabled={busy}
                    >
                      <option value="creator">Creator</option>
                      <option value="reviewer">Reviewer</option>
                    </select>
                  </label>
                ) : (
                  <Badge variant="role">{member.role}</Badge>
                )}
                <Badge
                  variant={member.status === "active" ? "success" : "neutral"}
                >
                  {member.status}
                </Badge>
                {owner && member.role !== "owner" && (
                  <button
                    className="button ghost compact"
                    disabled={busy}
                    onClick={() =>
                      void update(
                        member,
                        member.role,
                        member.status === "active" ? "disabled" : "active",
                      )
                    }
                  >
                    {member.status === "active" ? "Disable" : "Restore"}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
        {owner && (
          <div className="invite-section">
            <h3>Invite a teammate</h3>
            <form className="invite-form" onSubmit={invite}>
              <label>
                Email address
                <input
                  name="email"
                  type="email"
                  required
                  placeholder="teammate@company.com"
                />
              </label>
              <label>
                Role
                <select name="role">
                  <option value="creator">Creator</option>
                  <option value="reviewer">Reviewer</option>
                </select>
              </label>
              <button className="button primary" disabled={busy}>
                Create invitation
              </button>
            </form>
            {token && (
              <div className="invitation-result">
                <label>
                  Invitation code
                  <input
                    readOnly
                    value={token}
                    onFocus={(e) => e.target.select()}
                  />
                </label>
                <button
                  className="button secondary compact"
                  onClick={() => {
                    void navigator.clipboard
                      .writeText(token)
                      .then(() => setSuccess("Invitation code copied."))
                      .catch(() =>
                        setError(
                          "Copy unavailable. Select and copy the invitation code manually.",
                        ),
                      );
                  }}
                >
                  <Copy size={14} />
                  Copy code
                </button>
                <p>
                  The teammate signs up with the matching email, then enters
                  this code in “Add or join organisation”. No email invitation
                  is sent automatically.
                </p>
              </div>
            )}
          </div>
        )}
      </section>
      <Diagnostic org={org} />
      <div className="foundation-note">
        <ShieldCheck size={17} />
        <p>
          This prototype uses email and password sign-in. Email ownership is not
          verified, and external AI processing is not configured.
        </p>
      </div>
    </>
  );
}

function Diagnostic({ org }: { org: Organisation }) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Not run");
  const [steps, setSteps] = useState<string[]>([]);
  const [snapshot, setSnapshot] = useState<{
    stepsCompleted: number;
    guidelineVersions: number;
  } | null>(null);
  const [error, setError] = useState("");
  const agent = useRef<HttpAgent | null>(null);
  const runId = useRef<string | null>(null);
  const cancelled = useRef(false);
  const mounted = useRef(true);
  const key = `inkloom-diagnostic:${org.id}`;
  const base = `/organisations/${org.id}/diagnostics`;
  useEffect(() => {
    mounted.current = true;
    const id = sessionStorage.getItem(key);
    if (id) {
      runId.current = id;
      void api<{ status: string }>(`${base}/runs/${id}`)
        .then((result) => {
          if (mounted.current) setStatus(`Saved status: ${result.status}`);
        })
        .catch((e) => {
          if (mounted.current) setError(message(e));
        });
    }
    return () => {
      mounted.current = false;
      agent.current?.abortRun();
    };
  }, [key, base]);
  async function start() {
    cancelled.current = false;
    setBusy(true);
    setError("");
    setSteps([]);
    setSnapshot(null);
    setStatus("Connecting…");
    const id = crypto.randomUUID();
    runId.current = id;
    sessionStorage.setItem(key, id);
    const client = new HttpAgent({
      url: `/api${base}/stream`,
      threadId: crypto.randomUUID(),
      headers: { "X-Inkloom-CSRF": "1" },
    });
    agent.current = client;
    try {
      await client.runAgent(
        { runId: id },
        {
          onStateSnapshotEvent: ({ event }) => {
            if (mounted.current && !cancelled.current)
              setSnapshot(
                event.snapshot as {
                  stepsCompleted: number;
                  guidelineVersions: number;
                },
              );
          },
          onStepStartedEvent: ({ event }) => {
            if (mounted.current && !cancelled.current)
              setStatus(event.stepName);
          },
          onStepFinishedEvent: ({ event }) => {
            if (mounted.current && !cancelled.current)
              setSteps((previous) =>
                previous.includes(event.stepName)
                  ? previous
                  : [...previous, event.stepName],
              );
          },
          onRunFinishedEvent: () => {
            if (mounted.current && !cancelled.current) setStatus("Completed");
          },
          onRunErrorEvent: ({ event }) => {
            if (mounted.current && !cancelled.current) setError(event.message);
          },
        },
      );
    } catch (e) {
      if (mounted.current && !cancelled.current) {
        setError(message(e));
        setStatus("Disconnected — checking saved status");
      }
    } finally {
      if (mounted.current) {
        setBusy(false);
        try {
          const result = await api<{ status: string }>(`${base}/runs/${id}`);
          setStatus(
            result.status === "completed"
              ? "Completed"
              : `Saved status: ${result.status}`,
          );
        } catch (e) {
          setError(message(e));
        }
      }
    }
  }
  async function cancel() {
    cancelled.current = true;
    agent.current?.abortRun();
    setStatus("Cancelling…");
    try {
      await api(`${base}/runs/${runId.current}/cancel`, send("POST"));
      setStatus("Cancelled");
    } catch (e) {
      if (!message(e).includes("already ended")) setError(message(e));
    }
    setBusy(false);
  }
  return (
    <section className="panel settings-section">
      <div className="section-heading">
        <div>
          <h2>
            <Activity size={20} />
            Connection check
          </h2>
          <p className="muted">
            A foundation diagnostic for progress streaming. This does not review
            content or call an AI model.
          </p>
        </div>
        <Badge>Diagnostic only</Badge>
      </div>
      {error && <Notice kind="error">{error}</Notice>}
      <div className="diagnostic-status" role="status" aria-live="polite">
        <span className={`status-dot ${busy ? "pulse" : ""}`} />
        {status}
      </div>
      {snapshot && (
        <p className="muted">
          {snapshot.stepsCompleted} of 3 steps complete ·{" "}
          {snapshot.guidelineVersions} guideline versions available
        </p>
      )}
      {steps.length > 0 && (
        <ul className="diagnostic-steps">
          {steps.map((step) => (
            <li key={step}>
              <Check size={15} />
              {step}
            </li>
          ))}
        </ul>
      )}
      <div className="form-actions">
        <button className="button secondary" onClick={start} disabled={busy}>
          <Play size={15} />
          Run connection check
        </button>
        {busy && (
          <button className="button ghost" onClick={cancel}>
            <Square size={14} />
            Cancel check
          </button>
        )}
      </div>
    </section>
  );
}

export function ActivityPage({ org }: { org: Organisation }) {
  const [events, setEvents] = useState<AuditEvent[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const abort = new AbortController();
    api<AuditEvent[]>(`/organisations/${org.id}/audit`, {
      signal: abort.signal,
    })
      .then(setEvents)
      .catch((e) => {
        if (!abort.signal.aborted) setError(message(e));
      });
    return () => abort.abort();
  }, [org.id]);
  return (
    <>
      <PageHeading title="Workspace activity">
        A permanent record of who changed what and when.
      </PageHeading>
      {error ? (
        <Notice kind="error">{error}</Notice>
      ) : !events ? (
        <Loading />
      ) : (
        <section className="panel">
          {events.length ? (
            <div className="activity-list">
              {events.map((event) => (
                <div className="activity-row" key={event.id}>
                  <span className="activity-icon">
                    <Activity size={17} />
                  </span>
                  <div>
                    <strong>
                      {event.action.replaceAll(".", " ").replaceAll("_", " ")}
                    </strong>
                    <small>
                      {event.actor_name} ·{" "}
                      {event.target_type.replaceAll("_", " ")}
                    </small>
                  </div>
                  <time dateTime={event.created_at}>
                    {date(event.created_at)}
                  </time>
                </div>
              ))}
            </div>
          ) : (
            <Empty title="No activity yet">
              Organisation changes will appear here.
            </Empty>
          )}
        </section>
      )}
    </>
  );
}
