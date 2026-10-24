"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Upload, Plus, Check, FileText } from "lucide-react";
import type { Organisation, Version } from "../../../packages/contracts";
import type {
  KnowledgeRule,
  KnowledgeSource,
  KnowledgeView,
} from "../../../packages/contracts/knowledge";
import { api, message, send } from "@/lib/api";
import { Badge, Loading, Notice, PageHeading } from "./ui";
import { CheckOptions, CoverageList } from "./check-options";
import ProposalFields from "./proposal-fields";

function SourceEvidence({
  rule,
  source,
}: {
  rule: KnowledgeRule;
  source?: KnowledgeSource;
}) {
  const location = source?.locations?.find(
    (l) =>
      l.location === rule.source_location ||
      l.text.includes(rule.source_excerpt || "\u0000"),
  );
  const excerpt = rule.source_excerpt || "",
    context = location?.text || excerpt,
    index = excerpt ? context.indexOf(excerpt) : -1;
  return (
    <div className="source-evidence">
      <small>
        {source?.filename ||
          (rule.source_document_id
            ? "Stored company source"
            : "Company-entered rule")}
        {rule.source_location ? ` · ${rule.source_location}` : ""}
      </small>
      {excerpt && (
        <blockquote>
          {index >= 0 ? (
            <>
              {context.slice(Math.max(0, index - 160), index)}
              <mark>{excerpt}</mark>
              {context.slice(
                index + excerpt.length,
                index + excerpt.length + 160,
              )}
            </>
          ) : (
            <mark>{excerpt}</mark>
          )}
        </blockquote>
      )}
      {source?.media_type?.startsWith("image/") && source.download_url && (
        <img
          className="source-reference"
          src={source.download_url}
          alt={`Source reference: ${source.filename}`}
        />
      )}
      {source?.download_url && (
        <a href={source.download_url} target="_blank" rel="noreferrer">
          Open original source
        </a>
      )}
    </div>
  );
}
export default function SourceSetup({ org }: { org: Organisation }) {
  const base = `/organisations/${org.id}/knowledge`;
  const [view, setView] = useState<
      | (KnowledgeView & { version: NonNullable<KnowledgeView["version"]> })
      | null
    >(null),
    [versions, setVersions] = useState<Version[]>([]);
  const [checks, setChecks] = useState<string[]>([]),
    [instructions, setInstructions] = useState("");
  const [selected, setSelected] = useState<string[]>([]),
    [replacements, setReplacements] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [ack, setAck] = useState(false),
    [newVersion, setNewVersion] = useState(false),
    [noVersion, setNoVersion] = useState(false);
  const [editingProposal, setEditingProposal] = useState<string | null>(null),
    [guidanceFormKey, setGuidanceFormKey] = useState(0);
  const input = useRef<HTMLInputElement>(null),
    owner = org.role === "owner" && view?.version.status !== "archived";
  const install = useCallback((data: KnowledgeView, preferences = true) => {
    if (!data.version) {
      setNoVersion(true);
      setView(null);
      setChecks(data.checks || []);
      setInstructions(data.instructions || "");
      return;
    }
    setNoVersion(false);
    setView({ ...data, version: data.version });
    if (preferences) {
      setChecks(data.checks || []);
      setInstructions(data.instructions || "");
    }
  }, []);
  const load = useCallback(
    async (versionId?: string, preferences = true) => {
      const data = await api<KnowledgeView>(
        `${base}${versionId ? `?version_id=${encodeURIComponent(versionId)}` : ""}`,
      );
      install(data, preferences);
      return data;
    },
    [base, install],
  );
  useEffect(() => {
    void load().catch((e) => setError(message(e)));
    void api<Version[]>(`/organisations/${org.id}/guidelines/versions`)
      .then(setVersions)
      .catch(() => {});
  }, [load, org.id]);
  const extracting =
    !!view &&
    ["queued", "running", "analysing", "processing"].includes(
      view.extraction.status,
    );
  useEffect(() => {
    if (!extracting || !view) return;
    const timer = setInterval(() => {
      void load(view.version.id, false).catch((e) => setError(message(e)));
    }, 1600);
    return () => clearInterval(timer);
  }, [extracting, load, view?.version.id]);
  async function work(name: string, action: () => Promise<void>) {
    setBusy(name);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy("");
    }
  }
  async function savePreferences() {
    if (!view) return;
    install(
      await api<KnowledgeView>(
        `${base}/preferences`,
        send("POST", { version_id: view.version.id, checks, instructions }),
      ),
    );
  }
  const proposals = (view?.proposals || []).filter(
    (p) => !p.status || ["pending", "proposed", "staged"].includes(p.status),
  );
  const preferenceDirty =
    !!view &&
    (JSON.stringify(checks) !== JSON.stringify(view.checks) ||
      instructions !== view.instructions);
  const canConfirm =
    !editingProposal &&
    selected.length > 0 &&
    selected.every((id) => {
      const p = proposals.find((p) => p.id === id);
      return (
        p && (!p.existing_rule_id || replacements[id] === p.existing_rule_id)
      );
    });
  return (
    <>
      <PageHeading
        title="Rules"
        action={
          org.role === "owner" && (
            <button
              className="button secondary"
              disabled={!!busy || extracting}
              onClick={() => setNewVersion(!newVersion)}
            >
              <Plus size={16} />
              New version
            </button>
          )
        }
      >
        Choose what matters, add company sources and confirm the rules your team
        will use.
      </PageHeading>
      {error && <Notice kind="error">{error}</Notice>}
      {notice && <Notice kind="success">{notice}</Notice>}
      {newVersion && (
        <section className="panel inline-confirm">
          <h2>Start an empty version?</h2>
          <p>
            This creates a new version without sources, rules or selected
            checks. Existing versions and their review history stay available.
          </p>
          <div className="form-actions">
            <button
              className="button primary"
              disabled={!!busy}
              onClick={() =>
                work("new", async () => {
                  install(
                    await api<KnowledgeView>(
                      `${base}/new-version`,
                      send("POST"),
                    ),
                  );
                  setSelected([]);
                  setReplacements({});
                  setAck(false);
                  setNewVersion(false);
                  setNotice(
                    "Empty version created. Add and confirm its rules before using it for reviews.",
                  );
                  setVersions(
                    await api<Version[]>(
                      `/organisations/${org.id}/guidelines/versions`,
                    ),
                  );
                })
              }
            >
              Create empty version
            </button>
            <button
              className="button secondary"
              onClick={() => setNewVersion(false)}
            >
              Cancel
            </button>
          </div>
        </section>
      )}
      {noVersion ? (
        <>
          <section className="rules-section">
            <h2>What should we check?</h2>
            <p className="muted">
              Create the first version, then choose your company’s default
              checks.
            </p>
            <CheckOptions value={checks} onChange={setChecks} disabled />
          </section>
          <section className="rules-section">
            <h2>Company sources</h2>
            <p>
              No sources yet. Start a version to add company documents and
              images.
            </p>
            {owner && (
              <button
                className="button primary"
                disabled={!!busy}
                onClick={() =>
                  work("first", async () => {
                    const data = await api<KnowledgeView>(
                      `${base}/new-version`,
                      send("POST"),
                    );
                    if (!data.version)
                      throw new Error(
                        "The first version could not be created.",
                      );
                    install(
                      await api<KnowledgeView>(
                        `${base}/preferences`,
                        send("POST", {
                          version_id: data.version.id,
                          checks,
                          instructions,
                        }),
                      ),
                    );
                  })
                }
              >
                Create first version
              </button>
            )}
          </section>
          <section className="rules-section">
            <h2>Review what was found</h2>
            <p className="muted">
              Proposed rules will appear here for human confirmation.
            </p>
          </section>
          <section className="rules-section">
            <h2>Confirmed current rules</h2>
            <p className="muted">There are no confirmed company rules yet.</p>
          </section>
        </>
      ) : !view ? (
        <Loading text="Loading company sources…" />
      ) : (
        <>
          <div className="rules-version-bar">
            <span>
              Version {view.version.version}{" "}
              <Badge>{view.version.status}</Badge>
            </span>
            {versions.length > 1 && (
              <label className="inline-label">
                View version
                <select
                  aria-label="View rule version"
                  value={view.version.id}
                  disabled={!!busy}
                  onChange={(e) =>
                    work("load", async () => {
                      await load(e.target.value);
                      setSelected([]);
                      setReplacements({});
                      setAck(false);
                    })
                  }
                >
                  {versions.map((v) => (
                    <option value={v.id} key={v.id}>
                      Version {v.version} · {v.status}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          {!owner && (
            <Notice>
              {view.version.status === "archived"
                ? "This historical version is read-only. Select the current version or start a new one to change company guidance."
                : "An organisation owner confirms changes to company rules. You can inspect the current sources and guidance here."}
            </Notice>
          )}
          <section className="rules-section" aria-labelledby="checks-heading">
            <div className="section-heading">
              <div>
                <h2 id="checks-heading">What should we check?</h2>
                <p>
                  These defaults appear on each new review. A review can use a
                  smaller selection.
                </p>
              </div>
            </div>
            <CheckOptions
              value={checks}
              onChange={(v) => {
                setChecks(v);
                setAck(false);
              }}
              disabled={!owner || !!busy}
            />
            <label className="expectations-label">
              Anything else we should look for?{" "}
              <textarea
                rows={3}
                maxLength={4000}
                placeholder="Optional expectations, such as a calm and direct tone."
                value={instructions}
                disabled={!owner || !!busy}
                onChange={(e) => {
                  setInstructions(e.target.value);
                  setAck(false);
                }}
              />
              <small>
                Instructions guide the check. Company facts still need approved
                evidence.
              </small>
            </label>
            {owner && (
              <button
                className="button secondary"
                disabled={!!busy || !preferenceDirty}
                onClick={() =>
                  work("preferences", async () => {
                    await savePreferences();
                    setNotice("Check preferences saved.");
                  })
                }
              >
                {busy === "preferences" ? "Saving…" : "Save preferences"}
              </button>
            )}
          </section>
          <section className="rules-section" aria-labelledby="sources-heading">
            <div className="section-heading">
              <div>
                <h2 id="sources-heading">Company sources</h2>
                <p>
                  Add documents, logos and reference images to this version.
                  Guidance is combined across all sources.
                </p>
              </div>
            </div>
            {owner && (
              <>
                <label className="source-upload">
                  <Upload size={23} />
                  <span>
                    <strong>Add company sources</strong>
                    <small>
                      PDF, DOCX, PNG or JPEG · maximum 5 MB each · videos
                      unsupported
                    </small>
                  </span>
                  <input
                    ref={input}
                    aria-label="Add company sources"
                    type="file"
                    accept=".pdf,.docx,.png,.jpg,.jpeg"
                    multiple
                    disabled={!!busy || extracting}
                    onChange={(e) => {
                      const files = Array.from(e.target.files || []);
                      if (!files.length) return;
                      void work("upload", async () => {
                        if (preferenceDirty) await savePreferences();
                        for (const file of files) {
                          const body = new FormData();
                          body.set("version_id", view.version.id);
                          body.set("file", file);
                          await api(`${base}/sources`, {
                            method: "POST",
                            body,
                          });
                        }
                        await load(view.version.id);
                        setNotice(
                          "Sources saved. Review the proposed rules below, or analyse the collection for additional guidance.",
                        );
                        if (input.current) input.current.value = "";
                      });
                    }}
                  />
                </label>
                <p className="muted source-limits">
                  Up to 10 sources per version. PDF intake supports up to 100
                  pages and 200,000 extracted characters per file. Split larger
                  materials into supported files.
                </p>
                <div className="form-actions">
                  <button
                    className="button secondary"
                    disabled={!!busy || extracting || !view.sources.length}
                    onClick={() =>
                      work("analyse", async () => {
                        if (preferenceDirty) await savePreferences();
                        await api(
                          `${base}/analyse`,
                          send("POST", { version_id: view.version.id }),
                        );
                        await load(view.version.id);
                      })
                    }
                  >
                    {extracting
                      ? "Reading sources…"
                      : busy === "upload"
                        ? "Uploading sources…"
                        : view.extraction.status === "partial"
                          ? "Continue source analysis"
                          : "Analyse sources"}
                  </button>
                  <small>
                    External AI analysis requires the processing consent in
                    Settings.
                  </small>
                </div>
              </>
            )}
            <p className="source-analysis-state" role="status">
              Source analysis: {view.extraction.status.replaceAll("_", " ")}
              {typeof view.extraction.processed === "number" &&
              typeof view.extraction.total === "number"
                ? ` · ${view.extraction.processed} of ${view.extraction.total} text chunks processed`
                : ""}
              .
            </p>
            {view.extraction.error && (
              <Notice kind="error">{view.extraction.error}</Notice>
            )}
            <div className="source-files">
              {view.sources.length ? (
                view.sources.map((s) => (
                  <details key={s.id} className="source-file">
                    <summary>
                      <FileText size={16} />
                      {s.filename}
                      <Badge>{s.extraction_status || "Stored"}</Badge>
                    </summary>
                    {s.media_type?.startsWith("image/") && s.download_url && (
                      <img
                        className="source-reference"
                        src={s.download_url}
                        alt={`Company reference: ${s.filename}`}
                      />
                    )}
                    <small>
                      {s.locations?.length || 0} extracted locations
                    </small>
                    {s.download_url && (
                      <a href={s.download_url} target="_blank" rel="noreferrer">
                        Open original source
                      </a>
                    )}
                  </details>
                ))
              ) : (
                <p className="muted">
                  No sources yet. Upload your price list, brand guide or visual
                  references.
                </p>
              )}
            </div>
            <h3>Coverage across this collection</h3>
            <CoverageList rows={view.coverage} />
            <p className="muted">
              Missing guidance stays visible. Supported checks can proceed; a
              missing source is never counted as a pass. Static visual comparison
              currently supports up to four confirmed image references per collection.
            </p>
          </section>
          {owner && (
            <section
              className="rules-section"
              aria-labelledby="manual-guidance-heading"
            >
              <h2 id="manual-guidance-heading">Add company guidance</h2>
              <p className="muted">
                Fill a missing field or add guidance your company wants checked.
                This stays proposed until you explicitly confirm it.
              </p>
              <ProposalFields
                key={`${view.version.id}-${guidanceFormKey}`}
                busy={!!busy}
                onSave={async (fields) => {
                  await work("manual", async () => {
                    await api(
                      `${base}/proposals`,
                      send("POST", { version_id: view.version.id, ...fields }),
                    );
                    await load(view.version.id, false);
                    setAck(false);
                    setGuidanceFormKey((key) => key + 1);
                    setNotice(
                      "Company-entered guidance added as a proposal. Review and confirm it below.",
                    );
                  });
                }}
              />
            </section>
          )}
          <section
            className="rules-section"
            aria-labelledby="proposals-heading"
          >
            <div className="section-heading">
              <div>
                <h2 id="proposals-heading">Review what was found</h2>
                <p>
                  Select the rules to include. Check each value and its source
                  before confirming.
                </p>
              </div>
              <Badge>{proposals.length} to review</Badge>
            </div>
            {owner && proposals.length > 1 && (
              <button
                className="button secondary compact select-proposals"
                disabled={!!busy}
                onClick={() => {
                  setSelected(proposals.map((p) => p.id));
                  setAck(false);
                }}
              >
                Select all proposed rules
              </button>
            )}
            {proposals.length ? (
              proposals.map((p) => {
                const old = view.rules.find((r) => r.id === p.existing_rule_id);
                return (
                  <article
                    className={`proposal ${selected.includes(p.id) ? "selected" : ""}`}
                    key={p.id}
                  >
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        disabled={!owner || !!busy}
                        checked={selected.includes(p.id)}
                        onChange={(e) => {
                          setSelected(
                            e.target.checked
                              ? [...selected, p.id]
                              : selected.filter((id) => id !== p.id),
                          );
                          setAck(false);
                        }}
                      />
                      <strong>{p.rule_key.replaceAll("_", " ")}</strong>
                      <Badge>
                        {p.existing_rule_id
                          ? "Replacement proposed"
                          : "Addition proposed"}
                      </Badge>
                    </label>
                    <div
                      className={p.existing_rule_id ? "rule-comparison" : ""}
                    >
                      {p.existing_rule_id && (
                        <div>
                          <small>Current confirmed rule</small>
                          <p>
                            {old?.value ||
                              "A current rule overlaps with this proposal."}
                          </p>
                          {old && (
                            <SourceEvidence
                              rule={old}
                              source={view.sources.find(
                                (s) => s.id === old.source_document_id,
                              )}
                            />
                          )}
                        </div>
                      )}
                      <div>
                        <small>
                          {p.existing_rule_id
                            ? "Proposed replacement"
                            : "Proposed value"}
                        </small>
                        <p>{p.value}</p>
                        <SourceEvidence
                          rule={p}
                          source={view.sources.find(
                            (s) => s.id === p.source_document_id,
                          )}
                        />
                      </div>
                    </div>
                    {owner &&
                      (editingProposal === p.id ? (
                        <ProposalFields
                          rule={p}
                          busy={!!busy}
                          onCancel={() => {
                            setEditingProposal(null);
                            setAck(false);
                          }}
                          onSave={async (fields) => {
                            await work("edit-proposal", async () => {
                              await api(
                                `${base}/proposals/${p.id}`,
                                send("PATCH", {
                                  version_id: view.version.id,
                                  ...fields,
                                }),
                              );
                              await load(view.version.id, false);
                              setEditingProposal(null);
                              setAck(false);
                              setReplacements((previous) => {
                                const next = { ...previous };
                                delete next[p.id];
                                return next;
                              });
                              setNotice(
                                "Proposed fields saved. Review the updated value and confirm it explicitly.",
                              );
                            });
                          }}
                        />
                      ) : (
                        <button
                          className="button ghost compact edit-proposal"
                          disabled={!!busy}
                          onClick={() => {
                            setEditingProposal(p.id);
                            setAck(false);
                          }}
                        >
                          Edit proposed fields
                        </button>
                      ))}
                    {p.existing_rule_id && (
                      <label className="checkbox-label replace-check">
                        <input
                          type="checkbox"
                          disabled={
                            !owner || !!busy || !selected.includes(p.id)
                          }
                          checked={replacements[p.id] === p.existing_rule_id}
                          onChange={(e) => {
                            setReplacements((v) => {
                              const result = { ...v };
                              if (e.target.checked)
                                result[p.id] = p.existing_rule_id!;
                              else delete result[p.id];
                              return result;
                            });
                            setAck(false);
                          }}
                        />
                        Replace this current rule with the proposed value.
                      </label>
                    )}
                  </article>
                );
              })
            ) : (
              <p className="muted">
                No pending proposals. Add sources or analyse the collection to
                find guidance.
              </p>
            )}
            {owner && (
              <div className="confirm-rules">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    disabled={!canConfirm || !!busy || preferenceDirty}
                    checked={ack}
                    onChange={(e) => setAck(e.target.checked)}
                  />
                  I reviewed the selected rules and their evidence, including
                  any replacements.
                </label>
                <div className="form-actions">
                  <button
                    className="button primary"
                    disabled={!!busy || !canConfirm || !ack || preferenceDirty}
                    onClick={() =>
                      work("confirm", async () => {
                        install(
                          await api<KnowledgeView>(
                            `${base}/confirm`,
                            send("POST", {
                              version_id: view.version.id,
                              proposal_ids: selected,
                              replace_rule_ids: Object.fromEntries(
                                Object.entries(replacements).filter(([id]) =>
                                  selected.includes(id),
                                ),
                              ),
                              expected_snapshot_id: view.snapshot_id,
                            }),
                          ),
                        );
                        setSelected([]);
                        setReplacements({});
                        setAck(false);
                        setNotice(
                          "Selected rules confirmed. New checks will use this approved knowledge snapshot.",
                        );
                      })
                    }
                  >
                    <Check size={16} />
                    {busy === "confirm"
                      ? "Confirming…"
                      : `Confirm selected rules${selected.length ? ` (${selected.length})` : ""}`}
                  </button>
                  {preferenceDirty && (
                    <small>Save your check preferences first.</small>
                  )}
                </div>
              </div>
            )}
          </section>
          <section
            className="rules-section"
            aria-labelledby="confirmed-heading"
          >
            <div className="section-heading">
              <div>
                <h2 id="confirmed-heading">Confirmed current rules</h2>
                <p>
                  Only human-confirmed rules provide authority for company
                  facts.
                </p>
              </div>
              <Badge>{view.rules.length} confirmed</Badge>
            </div>
            {view.rules.length ? (
              view.rules.map((r) => (
                <details className="confirmed-rule" key={r.id}>
                  <summary>
                    <strong>{r.rule_key.replaceAll("_", " ")}</strong>
                    <span>{r.value}</span>
                  </summary>
                  <SourceEvidence
                    rule={r}
                    source={view.sources.find(
                      (s) => s.id === r.source_document_id,
                    )}
                  />
                  <small>
                    To change a fact, add an updated source and explicitly
                    confirm its replacement. Historical checks keep their
                    original knowledge snapshot.
                  </small>
                </details>
              ))
            ) : (
              <p className="muted">No confirmed rules in this version.</p>
            )}
            <div className="form-actions">
              <Link
                href={`/org/${org.id}/reviews/new`}
                className="button primary"
              >
                Start a new review
              </Link>
              <small>
                Review tasks and human approval stay separate from rule
                confirmation.
              </small>
            </div>
          </section>
        </>
      )}
    </>
  );
}
