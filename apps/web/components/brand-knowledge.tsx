"use client";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  Plus,
  Upload,
  FileText,
  ShieldCheck,
  Check,
  Pencil,
  Trash2,
  ExternalLink,
  History,
} from "lucide-react";
import type {
  Organisation,
  Rule,
  RuleType,
  Version,
  VersionDetail,
} from "../../../packages/contracts";
import { api, date, message, send } from "@/lib/api";
import { Badge, Empty, Loading, Notice, PageHeading } from "./ui";

const types: Record<RuleType, string> = {
  approved_fact: "Approved fact",
  product_name: "Product name",
  prohibited_term: "Prohibited term",
  required_disclaimer: "Required disclaimer",
  tone: "Tone instruction",
  channel_instruction: "Channel instruction",
};
const tabs = [
  "Guidelines",
  "Approved facts",
  "Terms & tone",
  "Assets",
  "Version history",
];

export default function BrandKnowledge({ org }: { org: Organisation }) {
  const [versions, setVersions] = useState<Version[]>([]);
  const [selected, setSelected] = useState("");
  const [detail, setDetail] = useState<VersionDetail | null>(null);
  const [tab, setTab] = useState("Guidelines");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const base = `/organisations/${org.id}/guidelines/versions`;
  const owner = org.role === "owner";
  const editable = owner && detail?.status === "draft";
  const load = useCallback(
    async (id?: string) => {
      const list = await api<Version[]>(base);
      setVersions(list);
      const choice =
        id || list.find((v) => v.status === "draft")?.id || list[0]?.id || "";
      setSelected(choice);
      setDetail(choice ? await api<VersionDetail>(`${base}/${choice}`) : null);
    },
    [base],
  );
  useEffect(() => {
    let active = true;
    load()
      .catch((e) => {
        if (active) setError(message(e));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [load]);
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      await action();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function selectVersion(id: string) {
    setSelected(id);
    setDetail(null);
    setEditing(null);
    setAdding(false);
    await run(async () => {
      setDetail(await api<VersionDetail>(`${base}/${id}`));
    });
  }
  async function create() {
    await run(async () => {
      const v = await api<Version>(base, send("POST"));
      await load(v.id);
      setTab("Guidelines");
      setSuccess(
        `Version ${v.version} created. Add rules or upload a document.`,
      );
    });
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const file = new FormData(form);
    await run(async () => {
      const result = await api<{ message: string }>(
        `${base}/${selected}/uploads`,
        { method: "POST", body: file },
      );
      await load(selected);
      setSuccess(result.message);
      form.reset();
    });
  }
  async function activate() {
    if (
      !confirm(
        `Activate version ${detail?.version}? Its approved rules will be used for future reviews. The current active version will remain in history.`,
      )
    )
      return;
    await run(async () => {
      const r = await api<{ message: string }>(
        `${base}/${selected}/activate`,
        send("POST"),
      );
      await load(selected);
      setSuccess(r.message);
    });
  }
  async function discard(rule: Rule) {
    if (
      !confirm(
        "Discard this proposed rule? The source document and audit history will be kept.",
      )
    )
      return;
    await run(async () => {
      await api(`${base}/${selected}/rules/${rule.id}`, send("DELETE"));
      await load(selected);
      setSuccess("Proposed rule discarded.");
    });
  }
  async function save(event: FormEvent<HTMLFormElement>, rule?: Rule) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const body = {
      type: fields.get("type"),
      rule_key: fields.get("rule_key"),
      value: fields.get("value"),
      scope_channel: fields.get("scope_channel"),
      approved: fields.get("approved") === "on",
      revision: rule?.revision || 1,
      source_document_id: rule?.source_document_id || null,
      source_excerpt: rule?.source_excerpt || null,
      source_location: rule?.source_location || null,
      fact:
        fields.get("fact_enabled") === "on"
          ? {
              kind: "price",
              entity: fields.get("fact_entity"),
              amount: fields.get("fact_amount"),
              currency: fields.get("fact_currency"),
              unit: fields.get("fact_unit"),
              effective_from: fields.get("fact_date"),
              effective_to: null,
            }
          : null,
    };
    await run(async () => {
      await api(
        `${base}/${selected}/rules${rule ? `/${rule.id}` : ""}`,
        send(rule ? "PATCH" : "POST", body),
      );
      await load(selected);
      setEditing(null);
      setAdding(false);
      setSuccess("Rule saved.");
    });
  }
  if (loading) return <Loading text="Loading brand knowledge…" />;
  const filtered =
    detail?.rules.filter((rule) =>
      tab === "Approved facts"
        ? ["approved_fact", "product_name"].includes(rule.type)
        : tab === "Terms & tone"
          ? [
              "tone",
              "prohibited_term",
              "required_disclaimer",
              "channel_instruction",
            ].includes(rule.type)
          : true,
    ) || [];
  return (
    <>
      <PageHeading
        title="Brand knowledge"
        action={
          owner ? (
            <button className="button primary" disabled={busy} onClick={create}>
              <Plus size={17} />
              New version
            </button>
          ) : (
            <Badge>Read-only access</Badge>
          )
        }
      >
        The facts and guidelines your team can stand behind.
      </PageHeading>
      {error && <Notice kind="error">{error}</Notice>}
      {success && <Notice kind="success">{success}</Notice>}
      <div
        className="tabs"
        role="tablist"
        aria-label="Brand knowledge sections"
      >
        {tabs.map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            tabIndex={tab === t ? 0 : -1}
            onKeyDown={(event) => {
              const index = tabs.indexOf(t);
              const target =
                event.key === "ArrowRight"
                  ? (index + 1) % tabs.length
                  : event.key === "ArrowLeft"
                    ? (index + tabs.length - 1) % tabs.length
                    : event.key === "Home"
                      ? 0
                      : event.key === "End"
                        ? tabs.length - 1
                        : -1;
              if (target >= 0) {
                event.preventDefault();
                setTab(tabs[target]);
                (
                  event.currentTarget.parentElement?.children[
                    target
                  ] as HTMLButtonElement
                )?.focus();
              }
            }}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === "Assets" ? (
        <section className="panel">
          <Empty title="Brand assets are planned for a later phase">
            Logo storage and visual brand checks are not implemented in this
            foundation checkpoint. No uploaded image is analysed.
          </Empty>
        </section>
      ) : tab === "Version history" ? (
        <section className="panel">
          <div className="section-heading">
            <h2>Guideline versions</h2>
            <History size={20} />
          </div>
          {versions.length ? (
            versions.map((v) => (
              <button
                className="version-row"
                key={v.id}
                onClick={() => {
                  void selectVersion(v.id);
                  setTab("Guidelines");
                }}
              >
                <span>
                  <strong>Version {v.version}</strong>
                  <small>
                    {v.activated_at
                      ? `Activated ${date(v.activated_at)}`
                      : `Created ${date(v.created_at)}`}
                  </small>
                </span>
                <span>{v.rule_count} rules</span>
                <Badge variant={v.status === "active" ? "success" : "neutral"}>
                  {v.status}
                </Badge>
              </button>
            ))
          ) : (
            <Empty title="No versions yet">
              An owner can create the first guideline version.
            </Empty>
          )}
        </section>
      ) : !versions.length ? (
        <section className="panel">
          <Empty
            icon={<BookIcon />}
            title="Build your source of truth"
            action={
              owner ? (
                <button
                  className="button primary"
                  onClick={create}
                  disabled={busy}
                >
                  <Plus size={16} />
                  Create first version
                </button>
              ) : undefined
            }
          >
            Start with an approved facts document, or enter your brand rules
            manually. An owner reviews every rule before activation.
          </Empty>
        </section>
      ) : (
        <>
          <div className="version-toolbar">
            <label className="inline-label">
              Guideline version
              <select
                value={selected}
                onChange={(e) => void selectVersion(e.target.value)}
                disabled={busy}
              >
                {versions.map((v) => (
                  <option key={v.id} value={v.id}>
                    Version {v.version} · {v.status}
                  </option>
                ))}
              </select>
            </label>
            {detail && (
              <Badge
                variant={detail.status === "active" ? "success" : "neutral"}
              >
                {detail.status === "draft"
                  ? "Draft — not used for reviews"
                  : detail.status === "active"
                    ? "Active guidelines"
                    : "Historical · read-only"}
              </Badge>
            )}
            {editable && (
              <button
                className="button secondary"
                disabled={busy || !detail?.rules.length}
                onClick={activate}
              >
                <ShieldCheck size={17} />
                Activate version
              </button>
            )}
          </div>
          {!detail ? (
            <Loading text="Loading this version…" />
          ) : (
            <>
              <div className="knowledge-layout">
                <div className="rules-column">
                  <section className="panel rules-panel">
                    <div className="section-heading">
                      <div>
                        <h2>
                          {tab === "Guidelines"
                            ? "Rules for this version"
                            : tab}
                        </h2>
                        <p className="muted">
                          {editable
                            ? "Review the wording, category and evidence before approving."
                            : "Activated rules and their supporting sources remain traceable."}
                        </p>
                      </div>
                      {editable && (
                        <button
                          className="button secondary compact"
                          disabled={busy}
                          onClick={() => setAdding(!adding)}
                        >
                          <Plus size={16} />
                          Add rule
                        </button>
                      )}
                    </div>
                    {adding && (
                      <RuleForm
                        busy={busy}
                        onSubmit={(e) => save(e)}
                        onCancel={() => setAdding(false)}
                      />
                    )}
                    {filtered.length ? (
                      <div className="rule-list">
                        {filtered.map((rule) => (
                          <article className="rule-row" key={rule.id}>
                            <div className="rule-meta">
                              <Badge>{types[rule.type]}</Badge>
                              <Badge
                                variant={
                                  rule.approved_by ? "success" : "warning"
                                }
                              >
                                {rule.approved_by ? (
                                  <>
                                    <Check size={12} />
                                    Owner approved
                                  </>
                                ) : (
                                  "Needs owner review"
                                )}
                              </Badge>
                              <span className="rule-scope">
                                {rule.scope_channel}
                              </span>
                            </div>
                            {editing === rule.id ? (
                              <RuleForm
                                rule={rule}
                                busy={busy}
                                onSubmit={(e) => save(e, rule)}
                                onCancel={() => setEditing(null)}
                              />
                            ) : (
                              <>
                                <h3>{rule.rule_key.replaceAll("_", " ")}</h3>
                                <p className="rule-value">{rule.value}</p>
                                {rule.source_document_id ? (
                                  <details className="evidence">
                                    <summary>
                                      <FileText size={14} />
                                      {rule.source_location} · Source excerpt
                                    </summary>
                                    <blockquote>
                                      {rule.source_excerpt}
                                    </blockquote>
                                    <a
                                      href={`/api/organisations/${org.id}/sources/${rule.source_document_id}/download`}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      Download source
                                      <ExternalLink size={13} />
                                    </a>
                                  </details>
                                ) : (
                                  <p className="manual-source">
                                    Source: owner-entered rule
                                  </p>
                                )}
                                {editable && (
                                  <div className="rule-actions">
                                    <button
                                      className="button ghost compact"
                                      onClick={() => setEditing(rule.id)}
                                      disabled={busy}
                                    >
                                      <Pencil size={14} />
                                      Edit & review
                                    </button>
                                    <button
                                      className="button ghost compact danger"
                                      onClick={() => discard(rule)}
                                      disabled={busy}
                                    >
                                      <Trash2 size={14} />
                                      Discard
                                    </button>
                                  </div>
                                )}
                              </>
                            )}
                          </article>
                        ))}
                      </div>
                    ) : (
                      <Empty title="No rules here yet">
                        {editable
                          ? "Add a rule manually, or upload a document to propose source lines."
                          : "This version has no rules in this category."}
                      </Empty>
                    )}
                  </section>
                </div>
                <aside className="sources-column">
                  <section className="panel">
                    <div className="section-heading">
                      <h2>Source documents</h2>
                      <FileText size={18} />
                    </div>
                    {editable && (
                      <form className="upload-form" onSubmit={upload}>
                        <label className="file-input">
                          <Upload size={25} />
                          <strong>Add your guidelines</strong>
                          <small>Text-based PDF or DOCX · up to 5 MB</small>
                          <input
                            name="file"
                            type="file"
                            accept=".pdf,.docx"
                            required
                            aria-label="Select guideline document"
                          />
                        </label>
                        <button
                          className="button secondary full"
                          disabled={busy}
                        >
                          {busy ? "Processing…" : "Upload & extract text"}
                        </button>
                        <small>
                          Extracted source lines are proposals. No AI
                          interpretation is performed.
                        </small>
                      </form>
                    )}
                    {detail.sources.length ? (
                      detail.sources.map((source) => (
                        <div className="source-item" key={source.id}>
                          <FileText size={18} />
                          <div>
                            <strong>{source.filename}</strong>
                            <Badge
                              variant={
                                source.extraction_status === "partial"
                                  ? "warning"
                                  : "neutral"
                              }
                            >
                              {source.extraction_status === "partial"
                                ? "Partial text extraction"
                                : "Text extracted"}
                            </Badge>
                            <details>
                              <summary>Read extracted text</summary>
                              {source.locations.map((location, i) => (
                                <div className="source-excerpt" key={i}>
                                  <strong>{location.location}</strong>
                                  <p>
                                    {location.text ||
                                      "No text extracted from this page."}
                                  </p>
                                </div>
                              ))}
                            </details>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="muted source-empty">
                        No documents uploaded. Manually entered rules are
                        supported too.
                      </p>
                    )}
                  </section>
                  <section className="knowledge-help">
                    <ShieldCheck size={21} />
                    <h3>People set the standard.</h3>
                    <p>
                      Uploaded documents cannot activate themselves. Only your
                      organisation owner can approve rules and activate a
                      guideline version.
                    </p>
                    <p>
                      Older versions stay available when your knowledge changes.
                    </p>
                  </section>
                </aside>
              </div>
            </>
          )}
        </>
      )}
    </>
  );
}
function BookIcon() {
  return <FileText size={29} />;
}
function RuleForm({
  rule,
  busy,
  onSubmit,
  onCancel,
}: {
  rule?: Rule;
  busy: boolean;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}) {
  return (
    <form className="rule-form" onSubmit={onSubmit}>
      <div className="form-pair">
        <label>
          Rule type
          <select name="type" defaultValue={rule?.type || "approved_fact"}>
            {Object.entries(types).map(([key, value]) => (
              <option key={key} value={key}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Applies to
          <select
            name="scope_channel"
            defaultValue={rule?.scope_channel || "global"}
          >
            {[
              "global",
              "general",
              "linkedin",
              "instagram",
              "website",
              "email",
              "advertisement",
            ].map((c) => (
              <option key={c} value={c}>
                {c === "global" ? "All channels" : c}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label>
        Rule key
        <input
          name="rule_key"
          defaultValue={rule?.rule_key || ""}
          placeholder="e.g. monthly_price"
          required
          maxLength={100}
        />
        <small>
          Use the same key for the same fact so conflicting values can be
          detected.
        </small>
      </label>
      <label>
        Approved wording or value
        <textarea
          name="value"
          required
          maxLength={2000}
          rows={3}
          defaultValue={rule?.value || ""}
          placeholder="e.g. Rs 999/month, effective 23 October 2026"
        />
      </label>
      {rule?.source_excerpt && (
        <blockquote className="form-source">
          Source: {rule.source_excerpt}
        </blockquote>
      )}
      <details className="evidence" open={!!rule?.fact}>
        <summary>Exact price check (optional)</summary>
        <p>
          Enable only after verifying the product, unit, currency and effective
          date. Ambiguous free text remains a contextual AI/human check.
        </p>
        <label className="checkbox-label">
          <input
            type="checkbox"
            name="fact_enabled"
            defaultChecked={!!rule?.fact}
          />
          Enable this typed price fact
        </label>
        <div className="form-pair">
          <label>
            Exact product name
            <input
              name="fact_entity"
              defaultValue={rule?.fact?.entity || ""}
              maxLength={150}
            />
          </label>
          <label>
            Unit or size
            <input
              name="fact_unit"
              defaultValue={rule?.fact?.unit || ""}
              placeholder="e.g. 150ml or item"
              maxLength={80}
            />
          </label>
        </div>
        <div className="form-pair">
          <label>
            Approved amount
            <input
              name="fact_amount"
              type="number"
              min="0"
              step="0.01"
              defaultValue={rule?.fact?.amount || ""}
            />
          </label>
          <label>
            Currency
            <select
              name="fact_currency"
              defaultValue={rule?.fact?.currency || "INR"}
            >
              {["INR", "USD", "EUR", "GBP"].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Effective from
          <input
            name="fact_date"
            type="date"
            defaultValue={rule?.fact?.effective_from || ""}
          />
        </label>
      </details>
      <label className="checkbox-label">
        <input
          type="checkbox"
          name="approved"
          defaultChecked={!!rule?.approved_by}
        />
        <span>
          I reviewed this rule and approve it as an authoritative brand rule.
        </span>
      </label>
      <div className="form-actions">
        <button className="button primary compact" disabled={busy}>
          Save rule
        </button>
        <button
          type="button"
          className="button ghost compact"
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
