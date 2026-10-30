"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { HttpAgent } from "@ag-ui/client";
import {
  FileText,
  Upload,
  Save,
  Play,
  Square,
  Check,
  MessageSquare,
  History,
  ArrowLeft,
  Download,
  ShieldCheck,
  Search,
  ChevronRight,
} from "lucide-react";
import type { Organisation, User, Member } from "../../../packages/contracts";
import type {
  AiPreview,
  Draft,
  DraftVersion,
  Finding,
  ReviewRun,
  RewriteOption,
} from "../../../packages/contracts/reviews";
import type { DocumentEditorHandle } from "./document-editor";
import { api, date, message, send } from "@/lib/api";
import { Badge, Empty, Loading, Notice, PageHeading } from "./ui";
import { CheckOptions, CoverageList, InfoHelp } from "./check-options";
import type { KnowledgeView } from "../../../packages/contracts/knowledge";
import { checkLabel } from "../../../packages/contracts/knowledge";
import FindingAssistant from "./finding-assistant";
import DocumentChat from "./document-chat";
import VisualInspection from "./visual-inspection";
import VisualConfirmation from "./visual-confirmation";
import CampaignField from "./campaign-field";
const DocumentEditor = dynamic(() => import("./document-editor"), {
  ssr: false,
  loading: () => <Loading text="Opening the Word editor…" />,
});
const categories = [
  [
    "email",
    "Email",
    "Paste email copy or upload a DOCX, text PDF or static image.",
  ],
  [
    "social_media",
    "Social media",
    "Choose a platform, then paste a caption or upload a document or static image. Videos are unsupported.",
  ],
  [
    "visuals",
    "Ads & visuals",
    "Upload PNG or JPEG advertisements or screenshots. Static visual evaluation does not edit the image. Videos are unsupported.",
  ],
  [
    "website",
    "Website",
    "Paste website copy or upload a screenshot or document. Live URLs are not crawled.",
  ],
  [
    "documents",
    "Documents",
    "Upload DOCX for Word editing, text PDF for selectable text, or paste content.",
  ],
  [
    "other",
    "Other",
    "Paste text or upload DOCX, text PDF, PNG or JPEG. Videos are unsupported.",
  ],
] as const;
const platforms = [
  ["linkedin", "LinkedIn"],
  ["instagram", "Instagram"],
  ["x", "X"],
  ["facebook", "Facebook"],
  ["threads", "Threads"],
  ["tiktok", "TikTok"],
  ["youtube", "YouTube"],
  ["pinterest", "Pinterest"],
] as const;
const legacyChannel = (category: string, platform: string) =>
  category === "social_media"
    ? ["linkedin", "instagram"].includes(platform)
      ? platform
      : "general"
    : category === "visuals"
      ? "advertisement"
      : ["email", "website"].includes(category)
        ? category
        : "general";
const words = (text: string) =>
  text.trim().split(/\s+/u).filter(Boolean).length;
const label = (value: string) => value.replaceAll("_", " ");
const checksKey = (values: string[]) => [...values].sort().join(",");

export default function ReviewWorkspace({
  org,
  user,
  id,
}: {
  org: Organisation;
  user: User;
  id: string;
}) {
  const router = useRouter(),
    base = `/organisations/${org.id}`;
  const [draft, setDraft] = useState<Draft | null>(null),
    [text, setText] = useState(""),
    [title, setTitle] = useState("");
  const [category, setCategory] = useState("other"),
    [platform, setPlatform] = useState("");
  const [requestedChecks, setRequestedChecks] = useState<string[]>([]),
    [taskInstructions, setTaskInstructions] = useState("");
  const [knowledge, setKnowledge] = useState<KnowledgeView | null>(null);
  const [campaign, setCampaign] = useState("");
  const [format, setFormat] = useState("text"),
    [file, setFile] = useState<File | null>(null),
    [dirty, updateDirty] = useState(false),
    [editorReady, setEditorReady] = useState(false),
    [openedVersion, setOpenedVersion] = useState("");
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [tab, setTab] = useState("findings"),
    [mobileTab, setMobileTab] = useState("document");
  const [preview, setPreview] = useState<AiPreview | null>(null),
    [run, setRun] = useState<ReviewRun | null>(null),
    [progress, setProgress] = useState("");
  const [members, setMembers] = useState<Member[]>([]),
    [reviewer, setReviewer] = useState(""),
    [comment, setComment] = useState(""),
    [decisionComment, setDecisionComment] = useState(""),
    [visualAck, setVisualAck] = useState(false);
  const [transcriptConfirmed, setTranscriptConfirmed] = useState(false);
  const [revisionConflict, setRevisionConflict] = useState(false);
  const dirtyRef = useRef(false),
    displayedVersion = useRef("");
  const setDirty = useCallback((value: boolean) => {
    dirtyRef.current = value;
    updateDirty(value);
  }, []);
  const [options, setOptions] = useState<Record<string, RewriteOption[]>>({}),
    [rewriteRun, setRewriteRun] = useState<Record<string, string>>({});
  const editor = useRef<DocumentEditorHandle>(null),
    textArea = useRef<HTMLTextAreaElement>(null),
    agent = useRef<HttpAgent | null>(null),
    alive = useRef(true);
  const creating = id === "new";
  const load = useCallback(
    async (initial = false) => {
      const data = await api<Draft>(`${base}/drafts/${id}`);
      const changed = displayedVersion.current !== data.current_version_id;
      if (!initial && changed && dirtyRef.current) {
        setRevisionConflict(true);
        setPreview(null);
        setOptions({});
        return data;
      }
      setDraft(data);
      if (initial || changed) {
        displayedVersion.current = data.current_version_id;
        setText(data.current_version.text);
        setTitle(data.title);
        setCategory(
          data.category ||
            (platforms.some(([p]) => p === data.channel)
              ? "social_media"
              : data.channel === "advertisement"
                ? "visuals"
                : ["email", "website"].includes(data.channel)
                  ? data.channel
                  : data.format === "docx" || data.format === "pdf"
                    ? "documents"
                    : "other"),
        );
        setPlatform(
          data.platform ||
            (platforms.some(([p]) => p === data.channel) ? data.channel : ""),
        );
        if (data.requested_checks?.length)
          setRequestedChecks(data.requested_checks);
        else {
          const defaults = await api<KnowledgeView>(`${base}/knowledge`);
          setKnowledge(defaults);
          setRequestedChecks(defaults.checks || []);
        }
        setTaskInstructions(data.task_instructions || "");
        setOpenedVersion(data.current_version_id);
        setDirty(false);
        setRevisionConflict(false);
        setVisualAck(false);
        setTranscriptConfirmed(false);
        setEditorReady(false);
        setPreview(null);
        setOptions({});
      }
      const latest = data.runs.find((r) => r.run_kind === "review");
      if (latest)
        setRun(await api<ReviewRun>(`${base}/review-runs/${latest.id}`));
      else setRun(null);
      return data;
    },
    [base, id, setDirty],
  );
  useEffect(() => {
    alive.current = true;
    api<KnowledgeView>(`${base}/knowledge`)
      .then((data) => {
        setKnowledge(data);
        if (creating) setRequestedChecks(data.checks || []);
      })
      .catch((e) => setError(message(e)));
    if (!creating) {
      load(true).catch((e) => setError(message(e)));
      api<Member[]>(`${base}/members`)
        .then(setMembers)
        .catch((e) => setError(message(e)));
    }
    return () => {
      alive.current = false;
      agent.current?.abortRun();
    };
  }, [base, creating, load]);
  useEffect(() => {
    const leave = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", leave);
    return () => window.removeEventListener("beforeunload", leave);
  }, [dirty]);
  const running = run && ["queued", "running"].includes(run.status);
  useEffect(() => {
    if (!running || !run) return;
    let active = true;
    const timer = setInterval(() => {
      api<ReviewRun>(`${base}/review-runs/${run.id}`)
        .then((r) => {
          if (!active) return;
          setRun(r);
          setProgress(r.step);
          if (!["queued", "running"].includes(r.status)) void load();
        })
        .catch((e) => {
          if (active) setError(message(e));
        });
    }, 1500);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [base, run?.id, running, load]);
  async function work(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function create(e: FormEvent) {
    e.preventDefault();
    await work(async () => {
      if (!requestedChecks.length)
        throw new Error("Choose at least one check for this review.");
      let result: Draft;
      if (format === "text")
        result = await api<Draft>(
          `${base}/drafts`,
          send("POST", {
            title: title || "Untitled draft",
            channel: legacyChannel(category, platform),
            text,
            category,
            platform: category === "social_media" ? platform || null : null,
            requested_checks: requestedChecks,
            task_instructions: taskInstructions,
            campaign,
          }),
        );
      else {
        if (!file) throw new Error("Choose a document to upload.");
        const body = new FormData();
        body.set("file", file);
        body.set("title", title || file.name);
        body.set("channel", legacyChannel(category, platform));
        body.set("category", category);
        if (category === "social_media" && platform)
          body.set("platform", platform);
        body.set("requested_checks", JSON.stringify(requestedChecks));
        body.set("task_instructions", taskInstructions);
        body.set("campaign", campaign);
        result = await api<Draft>(`${base}/drafts/upload`, {
          method: "POST",
          body,
        });
      }
      router.push(`/org/${org.id}/reviews/${result.id}`);
    });
  }
  async function save() {
    if (!draft || revisionConflict) return;
    await work(async () => {
      if (draft.format === "docx") {
        const blob = await editor.current!.snapshot(),
          body = new FormData();
        body.set(
          "file",
          blob,
          draft.current_version.filename || "document.docx",
        );
        body.set("expected_current_version_id", draft.current_version_id);
        await api<DraftVersion>(`${base}/drafts/${draft.id}/file-versions`, {
          method: "POST",
          body,
        });
      } else if (draft.format === "image") {
        if (!transcriptConfirmed)
          throw new Error(
            "Confirm that the transcript matches the original image before saving.",
          );
        await api(
          `${base}/drafts/${draft.id}/transcript`,
          send("POST", {
            text,
            expected_current_version_id: draft.current_version_id,
            verified: true,
          }),
        );
        setTranscriptConfirmed(false);
      } else
        await api(
          `${base}/drafts/${draft.id}/versions`,
          send("POST", {
            text,
            expected_current_version_id: draft.current_version_id,
          }),
        );
      setDirty(false);
      setOptions({});
      await load(true);
      setNotice("New revision saved. Recheck before submitting for approval.");
    });
  }
  async function inspectPayload() {
    if (!draft || revisionConflict) return;
    await work(async () => {
      if (dirty) throw new Error("Save your edits before checking content.");
      if (!requestedChecks.length)
        throw new Error("Select at least one check for this review task.");
      if (scopeDirty) {
        await api(
          `${base}/drafts/${draft.id}/scope`,
          send("POST", {
            expected_current_version_id: draft.current_version_id,
            category,
            platform: category === "social_media" ? platform || null : null,
            requested_checks: requestedChecks,
            task_instructions: taskInstructions,
          }),
        );
        await load();
      }
      setPreview(await api<AiPreview>(`${base}/drafts/${draft.id}/ai-preview`));
    });
  }
  async function startReview() {
    if (
      !draft ||
      !preview ||
      revisionConflict ||
      scopeDirty ||
      dirtyRef.current
    )
      return;
    await work(async () => {
      const created = await api<ReviewRun>(
        `${base}/drafts/${draft.id}/reviews`,
        send("POST", {
          version_id: draft.current_version_id,
          preview_hash: preview.preview_hash,
          idempotency_key: crypto.randomUUID(),
        }),
      );
      setPreview(null);
      setRun(created);
      setProgress("Starting review");
      setMobileTab("findings");
      const client = new HttpAgent({
        url: `/api${base}/review-runs/${created.id}/stream`,
        threadId: draft.id,
        headers: { "X-Inkloom-CSRF": "1" },
      });
      agent.current = client;
      void client
        .runAgent(
          { runId: created.id },
          {
            onStepStartedEvent: ({ event }) => {
              if (alive.current) setProgress(event.stepName);
            },
            onRunErrorEvent: ({ event }) => {
              if (alive.current) setNotice(event.message);
            },
          },
        )
        .catch(() => {
          if (alive.current)
            setNotice(
              "Stream disconnected. Saved status will continue updating.",
            );
        })
        .finally(() => {
          if (alive.current) void load().catch((e) => setError(message(e)));
        });
    });
  }
  async function reveal(finding: Finding) {
    setMobileTab("document");
    if (draft?.format === "docx") await editor.current?.reveal(finding.quote);
    else {
      const area = textArea.current;
      if (!area) return;
      area.focus();
      const start = Array.from(text).slice(0, finding.start).join("").length;
      const end = Array.from(text).slice(0, finding.end).join("").length;
      area.setSelectionRange(start, end);
    }
  }
  async function rewrites(finding: Finding) {
    if (!draft || !run || revisionConflict || scopeDirty) return;
    await work(async () => {
      if (dirty || run.stale)
        throw new Error("Save and recheck before requesting corrections.");
      const p = await api<AiPreview>(`${base}/drafts/${draft.id}/ai-preview`);
      let result = await api<ReviewRun>(
        `${base}/review-runs/${run.id}/rewrites`,
        send("POST", {
          finding_id: finding.id,
          preview_hash: p.preview_hash,
          idempotency_key: crypto.randomUUID(),
        }),
      );
      setNotice("Preparing corrections and checking their safety…");
      for (
        let attempt = 0;
        attempt < 120 && ["queued", "running"].includes(result.status);
        attempt++
      ) {
        await new Promise((r) => setTimeout(r, 1500));
        if (!alive.current) return;
        result = await api<ReviewRun>(`${base}/review-runs/${result.id}`);
      }
      setOptions((v) => ({ ...v, [finding.id]: result.result.options || [] }));
      setRewriteRun((v) => ({ ...v, [finding.id]: result.id }));
      setNotice("");
      if (!result.result.options?.length)
        throw new Error(
          result.error ||
            "No correction passed the safety checks. Edit the text manually and recheck.",
        );
    });
  }
  async function apply(finding: Finding, option: RewriteOption) {
    if (!draft || revisionConflict || scopeDirty) return;
    await work(async () => {
      if (dirty)
        throw new Error(
          "Save or undo local edits before applying a correction.",
        );
      if (draft.format === "docx") {
        await editor.current!.apply(option.original, option.text);
        setDirty(true);
        setNotice(
          "Correction applied in the editor. Save and recheck this revision.",
        );
      } else {
        await api(
          `${base}/drafts/${draft.id}/apply-rewrite`,
          send("POST", {
            expected_current_version_id: draft.current_version_id,
            option_id: option.id,
          }),
        );
        await load(true);
        setNotice(
          "Correction saved as a new revision. Recheck before approval.",
        );
      }
      setOptions({});
    });
  }
  async function addComment(e: FormEvent) {
    e.preventDefault();
    if (!draft) return;
    await work(async () => {
      await api(
        `${base}/drafts/${draft.id}/comments`,
        send("POST", { version_id: draft.current_version_id, body: comment }),
      );
      setComment("");
      await load();
    });
  }
  async function submit() {
    if (!draft || revisionConflict || scopeDirty) return;
    await work(async () => {
      if (dirty) throw new Error("Save and recheck your edits first.");
      await api(
        `${base}/drafts/${draft.id}/approvals`,
        send("POST", {
          version_id: draft.current_version_id,
          reviewer_id: reviewer,
          idempotency_key: crypto.randomUUID(),
        }),
      );
      await load();
      setNotice("Sent to the selected reviewer.");
    });
  }
  async function decide(decision: string) {
    if (
      !draft ||
      revisionConflict ||
      scopeDirty ||
      dirtyRef.current ||
      (draft.format === "docx" && !editorReady)
    )
      return;
    const pending = draft.approval_requests.find((a) => a.status === "pending");
    if (!pending) return;
    await work(async () => {
      await api(
        `${base}/approvals/${pending.id}/decision`,
        send("POST", {
          expected_version_id: draft.current_version_id,
          artifact_sha256: draft.current_version.artifact_sha256,
          decision,
          comment: decisionComment,
          manual_visual_ack: visualAck,
        }),
      );
      await load();
      setNotice(
        decision === "approved"
          ? "This exact revision was approved by you."
          : "Decision recorded.",
      );
    });
  }
  const editable = draft?.creator_id === user.id;
  const requiresTranscript = requestedChecks.some(
    (check) => !["colours_fonts", "logos", "accessibility"].includes(check),
  );
  const scopeDirty =
    !!draft &&
    (checksKey(requestedChecks) !==
      checksKey(
        draft.requested_checks?.length
          ? draft.requested_checks
          : knowledge?.checks || [],
      ) ||
      taskInstructions !== (draft.task_instructions || "") ||
      category !==
        (draft.category ||
          (platforms.some(([p]) => p === draft.channel)
            ? "social_media"
            : draft.channel === "advertisement"
              ? "visuals"
              : ["email", "website"].includes(draft.channel)
                ? draft.channel
                : draft.format === "docx" || draft.format === "pdf"
                  ? "documents"
                  : "other")) ||
      platform !==
        (draft.platform ||
          (platforms.some(([p]) => p === draft.channel) ? draft.channel : "")));
  const stale =
    dirty ||
    scopeDirty ||
    revisionConflict ||
    run?.stale ||
    run?.version_id !== draft?.current_version_id;
  const eligible = members.filter(
    (m) =>
      m.status === "active" &&
      ["owner", "reviewer"].includes(m.role) &&
      m.user_id !== draft?.creator_id &&
      m.user_id !== draft?.current_version.author_id,
  );
  const findings = run?.result.findings || [];
  const pending = draft?.approval_requests.find((a) => a.status === "pending");
  const ready =
    run?.status === "completed" &&
    (draft?.format !== "docx" || editorReady) &&
    !stale &&
    !findings.some(
      (f) =>
        f.severity === "high" &&
        ["confirmed_mismatch", "conflicting_sources"].includes(f.status),
    ) &&
    (draft?.current_version.projection.coverage.text_complete ||
      (draft?.format === "image" &&
        (draft.requested_checks || []).length > 0 &&
        (draft.requested_checks || []).every((check) =>
          ["colours_fonts", "logos", "accessibility"].includes(check),
        ))) &&
    !draft?.current_version.projection.unresolved_changes;
  if (creating)
    return (
      <>
        <PageHeading title="New review">
          Choose where your content belongs and what you want checked.
        </PageHeading>
        {error && <Notice kind="error">{error}</Notice>}
        <form className="panel new-review-form" onSubmit={create}>
          <div className="form-pair">
            <label>
              Title
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={160}
                placeholder="e.g. Product launch announcement"
              />
            </label>
            <div className="field-with-help">
              <label htmlFor="review-category">Content category</label>
              <InfoHelp
                text={
                  categories.find(([key]) => key === category)?.[2] ||
                  "Choose the purpose of this content."
                }
                label="About this content category"
              />
              <select
                id="review-category"
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  if (e.target.value !== "social_media") setPlatform("");
                }}
              >
                {categories.map(([key, name]) => (
                  <option value={key} key={key}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {category === "social_media" && (
            <div className="field-with-help">
              <label htmlFor="review-platform">
                Platform <span className="muted">(optional)</span>
              </label>
              <InfoHelp
                text={`${platforms.find(([key]) => key === platform)?.[1] || "Social media"}: paste your caption or upload a static image, DOCX or text PDF. Platform selection describes where it will appear. Video uploads are unsupported, including for TikTok and YouTube.`}
                label="About this social platform"
              />
              <select
                id="review-platform"
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
              >
                <option value="">Choose platform</option>
                {platforms.map(([key, name]) => (
                  <option key={key} value={key}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <fieldset className="task-checks">
            <label>
              Campaign <span className="muted">(optional)</span>
              <input
                value={campaign}
                onChange={(e) => setCampaign(e.target.value)}
                maxLength={120}
                placeholder="e.g. Autumn launch"
              />
            </label>
            <legend>What should we check?</legend>
            <p className="muted">
              Company defaults are selected. Choose the checks for this task.
            </p>
            <CheckOptions
              value={requestedChecks}
              onChange={setRequestedChecks}
            />
            <label>
              Task instructions <span className="muted">(optional)</span>
              <textarea
                rows={2}
                maxLength={2000}
                value={taskInstructions}
                onChange={(e) => setTaskInstructions(e.target.value)}
                placeholder="For example: check the launch price and keep the tone direct."
              />
              <small>
                Instructions guide this task; they cannot override approved
                company facts.
              </small>
            </label>
            {knowledge && (
              <CoverageList
                rows={knowledge.coverage.filter((row) =>
                  requestedChecks.includes(row.check),
                )}
              />
            )}
          </fieldset>
          <div className="segmented" aria-label="Content format">
            <button
              type="button"
              aria-pressed={format === "text"}
              onClick={() => setFormat("text")}
            >
              <FileText size={17} />
              Write or paste text
            </button>
            <button
              type="button"
              aria-pressed={format === "document"}
              onClick={() => setFormat("document")}
            >
              <Upload size={17} />
              Upload document or image
            </button>
          </div>
          {format === "text" ? (
            <label>
              Your content
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={13}
                required
                maxLength={30000}
                placeholder="Paste the content you want to review…"
              />
            </label>
          ) : (
            <label className="file-input">
              <Upload size={25} />
              <strong>Choose a document or image</strong>
              <input
                type="file"
                accept=".docx,.pdf,.png,.jpg,.jpeg"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                required
              />
              <small>
                Maximum 5 MB. DOCX opens in the Word-style editor. PDFs use
                selectable text. PNG and JPEG use local OCR with transcript
                verification. Static images receive evaluation only. Videos are
                unsupported.
              </small>
            </label>
          )}
          <div className="form-actions">
            <button
              className="button primary"
              disabled={busy || !requestedChecks.length}
            >
              {busy ? "Saving…" : "Open review workspace"}
              <ChevronRight size={16} />
            </button>
            <span className="muted">
              Your content stays local until you explicitly start an AI check.
            </span>
          </div>
        </form>
      </>
    );
  if (!draft)
    return error ? <Notice kind="error">{error}</Notice> : <Loading />;
  const version = draft.current_version;
  return (
    <div className="review-page">
      <Link className="back-link" href={`/org/${org.id}/content`}>
        <ArrowLeft size={14} />
        Tracking
      </Link>
      <div className="review-heading">
        <div>
          <h1>{draft.title}</h1>
          <div className="review-meta">
            <Badge>
              {categories.find(([key]) => key === category)?.[1] ||
                label(draft.category || draft.channel)}
            </Badge>
            {draft.platform && (
              <Badge>
                {platforms.find(([key]) => key === draft.platform)?.[1] ||
                  draft.platform}
              </Badge>
            )}
            <Badge
              variant={draft.status === "approved" ? "success" : "neutral"}
            >
              {label(draft.status)}
            </Badge>
            <span>Revision {version.revision}</span>
            <span>{dirty ? "Unsaved changes" : "Saved"}</span>
          </div>
        </div>
        <div className="form-actions">
          {editable && draft.format !== "pdf" && (
            <button
              className="button secondary"
              disabled={
                busy ||
                revisionConflict ||
                (draft.format === "image"
                  ? !transcriptConfirmed ||
                    (!dirty &&
                      draft.current_version.projection.coverage.text_complete)
                  : !dirty) ||
                (draft.format === "docx" && !editorReady)
              }
              onClick={save}
            >
              <Save size={16} />
              {draft.format === "image" ? "Confirm transcript & save" : "Save"}
            </button>
          )}
          {editable && (
            <button
              className="button primary"
              disabled={
                busy ||
                revisionConflict ||
                !!running ||
                dirty ||
                (draft.format === "image" &&
                  !draft.current_version.projection.coverage.text_complete &&
                  requiresTranscript)
              }
              onClick={inspectPayload}
            >
              <Play size={15} />
              {run ? "Recheck content" : "Check content"}
            </button>
          )}
        </div>
      </div>
      {error && <Notice kind="error">{error}</Notice>}
      {notice && <Notice>{notice}</Notice>}
      <CampaignField
        key={`${draft.id}/${version.id}`}
        base={base}
        draftId={draft.id}
        versionId={version.id}
        initial={draft.campaign || ""}
        editable={editable}
      />
      <details className="panel review-task-settings">
        <summary>
          Review task ·{" "}
          {(draft.requested_checks?.length
            ? draft.requested_checks
            : knowledge?.checks || []
          )
            .map(checkLabel)
            .join(", ") || "Company defaults"}
        </summary>
        <p className="muted">
          Changing the checks or instructions requires a new check before
          approval.
        </p>
        <CheckOptions
          value={requestedChecks}
          onChange={(v) => {
            setRequestedChecks(v);
            setPreview(null);
            setOptions({});
          }}
          disabled={!editable || busy || !!running}
        />
        {!requestedChecks.length && (
          <small>Select at least one check before checking this task.</small>
        )}
        <label>
          Task instructions
          <textarea
            rows={2}
            maxLength={2000}
            value={taskInstructions}
            readOnly={!editable}
            disabled={busy || !!running}
            onChange={(e) => {
              setTaskInstructions(e.target.value);
              setPreview(null);
              setOptions({});
            }}
          />
        </label>
        {scopeDirty && (
          <small>
            Unsaved task settings. Check content saves these settings and opens
            the payload preview.
          </small>
        )}
      </details>
      {revisionConflict && (
        <Notice kind="error">
          A newer revision was saved in another session. Your unsaved edits
          still use the original revision. Copy or download them before
          reloading.{" "}
          <button
            className="button secondary"
            onClick={() => {
              if (
                window.confirm(
                  "Discard unsaved edits and open the latest saved revision?",
                )
              )
                void work(async () => {
                  await load(true);
                });
            }}
          >
            Reload latest revision
          </button>
        </Notice>
      )}
      {preview && (
        <section className="panel payload-preview">
          <h2>Review what leaves this machine</h2>
          <p>{preview.notice}</p>
          {!!preview.visual_images?.length && (
            <div className="visual-outbound-preview">
              <p>
                These original images will leave this machine. Image pixels
                cannot be redacted.
              </p>
              <div>
                {preview.visual_images.map((image, index) => (
                  <figure key={`${image.url}-${index}`}>
                    <img src={image.url} alt={image.label} />
                    <figcaption>{image.label}</figcaption>
                  </figure>
                ))}
              </div>
            </div>
          )}
          <p>
            <Badge>{preview.redacted_values} private values redacted</Badge>{" "}
            Guidelines v{preview.guideline_version}
          </p>
          <details>
            <summary>
              Inspect exact outbound content and approved excerpts
            </summary>
            <pre>{JSON.stringify(preview.payload, null, 2)}</pre>
          </details>
          <p className="muted">
            If any business secrets remain, cancel and edit the source content.
            {preview.policy_version.includes("-retention-")
              ? "This free North Mini Code request requires no training. Provider retention may apply; zero data retention is not guaranteed."
              : "This request uses free routes with ZDR and no data collection requirements."}
          </p>
          <div className="form-actions">
            <button
              className="button primary"
              disabled={busy}
              onClick={startReview}
            >
              {preview.visual_images?.length
                ? "Send this text and images & check"
                : "Send this payload & check"}
            </button>
            <button
              className="button secondary"
              onClick={() => setPreview(null)}
            >
              Cancel
            </button>
          </div>
          <small>
            Organisation processing approval is managed in{" "}
            <Link href={`/org/${org.id}/settings`}>Team & settings</Link>.
          </small>
        </section>
      )}
      {!version.projection.coverage.text_complete &&
        !(
          draft.format === "image" &&
          (draft.requested_checks || []).length > 0 &&
          (draft.requested_checks || []).every((check) =>
            ["colours_fonts", "logos", "accessibility"].includes(check),
          )
        ) && (
          <Notice kind="error">
            Some text regions are unsupported:{" "}
            {version.projection.coverage.unsupported.join(", ")}. Submission is
            blocked.
          </Notice>
        )}
      {!!version.projection.unresolved_changes && (
        <Notice>
          Resolve {version.projection.unresolved_changes} existing tracked
          changes in the editor, save and recheck before submitting.
        </Notice>
      )}
      <div className="review-mobile-tabs">
        <button
          aria-pressed={mobileTab === "document"}
          onClick={() => setMobileTab("document")}
        >
          Document
        </button>
        <button
          aria-pressed={mobileTab === "findings"}
          onClick={() => setMobileTab("findings")}
        >
          Findings & review
        </button>
      </div>
      <div className="review-grid">
        <section
          className={`document-panel ${mobileTab === "document" ? "mobile-visible" : ""}`}
          aria-label="Content editor"
          inert={busy || undefined}
        >
          {draft.format === "docx" &&
          version.projection.coverage.text_complete ? (
            <DocumentEditor
              ref={editor}
              url={`/api${base}/drafts/${draft.id}/versions/${openedVersion}/download`}
              name={user.name}
              email={user.email}
              readOnly={!editable}
              onReady={(url) => {
                if (url.endsWith(`/${displayedVersion.current}/download`))
                  setEditorReady(true);
              }}
              onDirty={() => setDirty(true)}
            />
          ) : (
            <>
              {draft.format === "image" && (
                <VisualInspection
                  key={version.id}
                  base={base}
                  draftId={draft.id}
                  versionId={version.id}
                  findings={stale ? [] : findings}
                />
              )}
              <div className="document-caption">
                <FileText size={16} />
                {draft.format === "pdf"
                  ? "PDF selectable text"
                  : draft.format === "docx"
                    ? "Read-only extracted text"
                    : draft.format === "image"
                      ? "Image transcript"
                      : "Draft content"}
                <span>{words(text)} words</span>
              </div>
              <textarea
                ref={textArea}
                className="draft-text"
                aria-label="Draft content"
                value={text}
                readOnly={
                  !editable || !["text", "image"].includes(draft.format)
                }
                onChange={(e) => {
                  setText(e.target.value);
                  setDirty(true);
                  setTranscriptConfirmed(false);
                }}
                maxLength={30000}
                spellCheck={false}
              />
              {draft.format === "image" && editable && (
                <div className="transcript-confirm">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={transcriptConfirmed}
                      onChange={(e) => setTranscriptConfirmed(e.target.checked)}
                    />
                    I compared every line with the original image and confirm
                    this transcript is accurate.
                  </label>
                  <small>
                    Transcript edits do not change the image. Upload a corrected
                    image to fix its printed content.
                  </small>
                </div>
              )}
            </>
          )}
          <div className="document-foot">
            <span>
              {dirty
                ? "Save before checking or submitting."
                : `Saved ${date(version.created_at)}`}
            </span>
            <a
              href={`/api${base}/drafts/${draft.id}/versions/${version.id}/download`}
              download
            >
              <Download size={14} />
              Download saved {draft.format.toUpperCase()}
            </a>
          </div>
        </section>
        <aside
          className={`review-side ${mobileTab === "findings" ? "mobile-visible" : ""}`}
          aria-label="Review findings and collaboration"
        >
          <div className="tabs" role="tablist" aria-label="Review panels">
            {[
              ["findings", "Findings", Search],
              ["comments", "Comments", MessageSquare],
              ["history", "History", History],
            ].map(([key, text, Icon]) => (
              <button
                key={String(key)}
                role="tab"
                aria-selected={tab === key}
                onClick={() => setTab(String(key))}
              >
                {String(text)}
              </button>
            ))}
          </div>
          {tab === "findings" && (
            <>
              <div className="review-state" aria-live="polite">
                <strong>
                  {running
                    ? progress || run.step
                    : stale && run
                      ? "Changes need a fresh check"
                      : run?.status === "completed"
                        ? "Check complete"
                        : run
                          ? label(run.status)
                          : "Ready when you are"}
                </strong>
                {running && (
                  <button
                    className="button ghost compact"
                    onClick={() =>
                      work(async () => {
                        await api(
                          `${base}/review-runs/${run.id}/cancel`,
                          send("POST"),
                        );
                        agent.current?.abortRun();
                        await load();
                      })
                    }
                  >
                    <Square size={13} />
                    Cancel
                  </button>
                )}
                <p>
                  {running
                    ? "Checking the saved revision against owner-approved knowledge."
                    : run?.status === "completed" && !stale
                      ? `${findings.length} findings. Supported checks do not guarantee compliance.`
                      : "Save your content, inspect the outbound payload, then start a check."}
                </p>
                {run?.error && <Notice kind="error">{run.error}</Notice>}
                {run?.result.mode === "local_checks_only" && (
                  <Badge variant="warning">
                    Local checks only · AI incomplete
                  </Badge>
                )}
                {run?.result.metadata && (
                  <small>
                    Model: {run.result.metadata.model} · Provider:{" "}
                    {run.result.metadata.provider || "not returned"}
                  </small>
                )}
              </div>
              {run?.result.check_coverage && (
                <CoverageList rows={run.result.check_coverage} />
              )}
              {draft.format === "image" && (
                <p className="muted">
                  Image evaluation only. The app does not rewrite or change
                  pixels.
                </p>
              )}
              {run && ["completed", "incomplete"].includes(run.status) && (
                <DocumentChat
                  key={run.id}
                  base={base}
                  runId={run.id}
                  disabled={!!stale || dirty || scopeDirty || !!running}
                />
              )}
              {findings.map((f) => (
                <article className="finding" key={f.id}>
                  <div className="finding-meta">
                    <Badge
                      variant={f.severity === "high" ? "warning" : "neutral"}
                    >
                      {f.severity}
                    </Badge>
                    <Badge>{label(f.status)}</Badge>
                    <span>{label(f.category)}</span>
                  </div>
                  <button className="finding-quote" onClick={() => reveal(f)}>
                    “{f.quote}”
                  </button>
                  <p>{f.reason}</p>
                  {f.evidence.length ? (
                    f.evidence.map((e) => (
                      <details className="evidence" key={e.id}>
                        <summary>
                          Source: {e.rule_key.replaceAll("_", " ")}
                        </summary>
                        <blockquote>{e.excerpt}</blockquote>
                        <small>
                          {e.location} · guideline{" "}
                          {run?.guideline_version_id.slice(0, 8)}
                        </small>
                        <p>Approved rule: {e.value}</p>
                        {(e.reference_url ||
                          e.source_download_url ||
                          knowledge?.sources.find(
                            (s) => s.id === e.source_document_id,
                          )?.download_url) && (
                          <a
                            target="_blank"
                            rel="noreferrer"
                            href={
                              e.reference_url ||
                              e.source_download_url ||
                              knowledge?.sources.find(
                                (s) => s.id === e.source_document_id,
                              )?.download_url
                            }
                          >
                            Open cited source
                          </a>
                        )}
                        {(e.media_type?.startsWith("image/") ||
                          knowledge?.sources
                            .find((s) => s.id === e.source_document_id)
                            ?.media_type?.startsWith("image/")) &&
                          (e.reference_url ||
                            e.source_download_url ||
                            knowledge?.sources.find(
                              (s) => s.id === e.source_document_id,
                            )?.download_url) && (
                            <img
                              className="source-reference"
                              src={
                                e.reference_url ||
                                e.source_download_url ||
                                knowledge?.sources.find(
                                  (s) => s.id === e.source_document_id,
                                )?.download_url
                              }
                              alt="Approved source image cited by this finding"
                            />
                          )}
                      </details>
                    ))
                  ) : (
                    <p className="muted">
                      No approved supporting evidence found. A human must verify
                      this claim.
                    </p>
                  )}
                  {f.evidence_validation && (
                    <small>{f.evidence_validation}</small>
                  )}
                  {run && (
                    <button
                      className="button ghost compact"
                      disabled={!!stale || dirty || scopeDirty || !!running}
                      onClick={() =>
                        window.dispatchEvent(
                          new CustomEvent("inkloom-document-chat", {
                            detail: {
                              runId: run.id,
                              question:
                                `Explain finding ${f.id}: ${f.quote}`.slice(
                                  0,
                                  500,
                                ),
                            },
                          }),
                        )
                      }
                    >
                      Discuss in document chat
                    </button>
                  )}
                  {run && (
                    <FindingAssistant
                      key={`${run.id}/${f.id}`}
                      base={base}
                      runId={run.id}
                      findingId={f.id}
                      disabled={!!stale || dirty || scopeDirty || !!running}
                    />
                  )}
                  {run && f.region && (
                    <VisualConfirmation
                      base={base}
                      runId={run.id}
                      findingId={f.id}
                      canConfirm={
                        org.role !== "creator" && draft.creator_id !== user.id
                      }
                      disabled={!!stale || dirty || scopeDirty || !!running}
                    />
                  )}
                  {editable && ["text", "docx"].includes(draft.format) && (
                    <div className="finding-actions">
                      <button
                        className="button secondary compact"
                        disabled={
                          busy || !!stale || run?.status !== "completed"
                        }
                        onClick={() => rewrites(f)}
                      >
                        Suggest corrections
                      </button>
                      <button
                        className="button ghost compact"
                        disabled={busy || !!stale || f.dismissed}
                        onClick={() =>
                          work(async () => {
                            const reason = window.prompt(
                              "Why are you dismissing this finding? This does not bypass approval checks.",
                            );
                            if (!reason) return;
                            await api(
                              `${base}/review-runs/${run!.id}/dismiss`,
                              send("POST", { finding_id: f.id, reason }),
                            );
                            await load();
                          })
                        }
                      >
                        {f.dismissed ? "Dismissed with note" : "Dismiss"}
                      </button>
                    </div>
                  )}
                  {options[f.id]?.map((o) => (
                    <div className="rewrite-option" key={o.id}>
                      <strong>{o.label}</strong>
                      <small>Original selection</small>
                      <blockquote>{o.original}</blockquote>
                      <small>Suggested correction</small>
                      <p>{o.text}</p>
                      <small>{o.length_note}</small>
                      <button
                        className="button secondary compact"
                        disabled={busy || !!stale}
                        onClick={() => apply(f, o)}
                      >
                        Apply correction
                      </button>
                    </div>
                  ))}
                </article>
              ))}
              {run?.status === "completed" && !findings.length && (
                <div className="quiet-state">
                  <Check size={22} />
                  <h3>No issues detected by supported checks</h3>
                  <p>A human still reviews and approves the saved content.</p>
                </div>
              )}
              <details className="coverage-detail">
                <summary>Review coverage</summary>
                <p>
                  Text:{" "}
                  {version.projection.coverage.text_complete
                    ? "Supported regions extracted completely"
                    : "Incomplete"}
                </p>
                <p>{version.projection.coverage.parts.join(", ")}</p>
                {version.projection.coverage.exclusions.map((x) => (
                  <p key={x}>{x}</p>
                ))}
                {run?.result.checks?.map((x) => (
                  <Badge key={x}>{x}</Badge>
                ))}
              </details>
              <section className="approval-box">
                <ShieldCheck size={21} />
                <h3>Human review</h3>
                {pending ? (
                  <>
                    <p>Waiting for {pending.reviewer_name}.</p>
                    {pending.reviewer_id === user.id && (
                      <>
                        <label>
                          Decision comment
                          <textarea
                            rows={3}
                            value={decisionComment}
                            onChange={(e) => setDecisionComment(e.target.value)}
                          />
                        </label>
                        {version.projection.coverage.exclusions.length > 0 && (
                          <label className="checkbox-label">
                            <input
                              type="checkbox"
                              checked={visualAck}
                              onChange={(e) => setVisualAck(e.target.checked)}
                            />
                            I personally inspected the excluded images and
                            layout in this exact saved document.
                          </label>
                        )}
                        <div className="form-actions">
                          <button
                            className="button primary"
                            disabled={busy || !ready}
                            onClick={() => decide("approved")}
                          >
                            Approve revision {version.revision}
                          </button>
                          <button
                            className="button secondary"
                            disabled={
                              busy ||
                              revisionConflict ||
                              dirty ||
                              scopeDirty ||
                              (draft.format === "docx" && !editorReady)
                            }
                            onClick={() => decide("needs_changes")}
                          >
                            Request changes
                          </button>
                          <button
                            className="button ghost danger"
                            disabled={
                              busy ||
                              revisionConflict ||
                              dirty ||
                              scopeDirty ||
                              (draft.format === "docx" && !editorReady)
                            }
                            onClick={() => decide("rejected")}
                          >
                            Reject
                          </button>
                        </div>
                      </>
                    )}
                  </>
                ) : draft.status === "approved" ? (
                  <p>
                    Approved revision {version.revision}. Download the saved
                    artifact for manual publication.
                  </p>
                ) : editable ? (
                  <>
                    <p>
                      {ready
                        ? "Choose a separate authorised reviewer."
                        : "Complete a fresh check and fix confirmed high-severity issues before submitting."}
                    </p>
                    {eligible.length ? (
                      <>
                        <label htmlFor="approval-reviewer">Reviewer</label>
                        <select
                          id="approval-reviewer"
                          value={reviewer}
                          onChange={(e) => setReviewer(e.target.value)}
                        >
                          <option value="">Choose a reviewer</option>
                          {eligible.map((m) => (
                            <option key={m.user_id} value={m.user_id}>
                              {m.name} · {m.role}
                            </option>
                          ))}
                        </select>
                        <button
                          className="button primary full"
                          disabled={busy || !ready || !reviewer}
                          onClick={submit}
                        >
                          Send for review
                        </button>
                      </>
                    ) : (
                      <p>
                        <Link href={`/org/${org.id}/settings`}>
                          Invite a reviewer
                        </Link>
                        . Authors cannot approve their own submissions.
                      </p>
                    )}
                  </>
                ) : (
                  <p>Approval controls appear for the assigned reviewer.</p>
                )}
              </section>
            </>
          )}
          {tab === "comments" && (
            <>
              <h3>Discuss this document</h3>
              {draft.comments.length ? (
                draft.comments.map((c) => (
                  <div className="review-comment" key={c.id}>
                    <strong>{c.actor_name}</strong>
                    <small>{date(c.created_at)}</small>
                    <p>{c.body}</p>
                  </div>
                ))
              ) : (
                <p className="muted">
                  No comments yet. Add context for your team.
                </p>
              )}
              <form onSubmit={addComment}>
                <label>
                  Comment
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    rows={4}
                    maxLength={3000}
                    required
                  />
                </label>
                <button className="button secondary" disabled={busy}>
                  Add comment
                </button>
              </form>
            </>
          )}
          {tab === "history" && (
            <>
              <h3>Saved revisions</h3>
              {draft.versions.map((v) => (
                <details className="history-entry" key={v.id}>
                  <summary>
                    Revision {v.revision} <small>{date(v.created_at)}</small>
                  </summary>
                  <pre>{v.text}</pre>
                  <a
                    href={`/api${base}/drafts/${draft.id}/versions/${v.id}/download`}
                  >
                    Download this revision
                  </a>
                  {editable && v.id !== draft.current_version_id && (
                    <button
                      className="button secondary compact"
                      disabled={busy || dirty}
                      onClick={() =>
                        work(async () => {
                          await api(
                            `${base}/drafts/${draft.id}/restore`,
                            send("POST", {
                              expected_current_version_id:
                                draft.current_version_id,
                              source_version_id: v.id,
                            }),
                          );
                          await load(true);
                          setOptions({});
                          setNotice(
                            "Restored as a new revision. Recheck before approval.",
                          );
                        })
                      }
                    >
                      Restore as new revision
                    </button>
                  )}
                </details>
              ))}
              <h3>Review history</h3>
              {draft.runs.map((r) => (
                <p key={r.id}>
                  {label(r.run_kind)} · {label(r.status)}
                  <small> {date(r.created_at)}</small>
                </p>
              ))}
              {draft.decisions.map((d) => (
                <div key={d.id} className="history-entry">
                  <strong>
                    {label(d.decision)} by {d.actor_name}
                  </strong>
                  <p>{d.comment}</p>
                  <small>
                    {date(d.created_at)} · artifact{" "}
                    {d.artifact_sha256.slice(0, 12)}
                  </small>
                </div>
              ))}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
