"use client";
import { useEffect, useRef, useState } from "react";
import { HttpAgent } from "@ag-ui/client";
import type { Evidence } from "../../../packages/contracts/reviews";
import { api, message, send } from "@/lib/api";
import { Badge, Notice } from "./ui";

interface ChatItem {
  finding_id: string;
  explanation: string;
  quote: string;
  reason: string;
  status: string;
  dismissed: boolean;
  evidence_missing: boolean;
  citations: Evidence[];
}
interface Turn {
  id: string;
  question: string;
  state: string;
  message?: string;
  items?: ChatItem[];
  notice?: string;
  error?: string;
  metadata?: { model?: string; provider?: string };
}
interface Preview {
  payload: unknown;
  preview_hash: string;
  redacted_values: number;
}

export default function DocumentChat({
  base,
  runId,
  disabled,
}: {
  base: string;
  runId: string;
  disabled: boolean;
}) {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [earlier, setEarlier] = useState(false);
  const [loading, setLoading] = useState(true);
  const [streamNote, setStreamNote] = useState("");
  const details = useRef<HTMLDetailsElement>(null);
  const active = useRef(true);
  const agent = useRef<HttpAgent | null>(null);
  const request = useRef<AbortController | null>(null);
  const requestKey = useRef("");
  const endpoint = `${base}/review-runs/${runId}/chat`;
  async function loadHistory() {
    const result = await api<{ turns: Turn[]; earlier_turns: boolean }>(
      endpoint,
    );
    if (active.current) {
      setTurns(result.turns);
      setEarlier(result.earlier_turns);
    }
  }
  useEffect(() => {
    active.current = true;
    function openLinkedChat() {
      if (window.location.hash === "#document-chat" && details.current)
        details.current.open = true;
    }
    openLinkedChat();
    window.addEventListener("hashchange", openLinkedChat);
    if (!disabled)
      void loadHistory()
        .catch((e) => {
          if (active.current) setError(message(e));
        })
        .finally(() => {
          if (active.current) setLoading(false);
        });
    else setLoading(false);
    function discuss(event: Event) {
      const selected = (
        event as CustomEvent<{ runId: string; question: string }>
      ).detail;
      if (selected.runId !== runId) return;
      setQuestion(selected.question);
      setPreview(null);
      if (details.current) {
        details.current.open = true;
        details.current.scrollIntoView({
          block: "nearest",
          behavior: "smooth",
        });
      }
    }
    window.addEventListener("inkloom-document-chat", discuss);
    return () => {
      active.current = false;
      request.current?.abort();
      agent.current?.abortRun();
      window.removeEventListener("inkloom-document-chat", discuss);
      window.removeEventListener("hashchange", openLinkedChat);
    };
    // Parent keys this component by review ID; stale changes cancel pending UI work.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, disabled, runId]);
  async function inspect(value: string) {
    setBusy(true);
    setError("");
    setPreview(null);
    setQuestion(value);
    request.current = new AbortController();
    try {
      const result = await api<Preview>(`${endpoint}/preview`, {
        ...send("POST", { question: value }),
        signal: request.current.signal,
      });
      if (active.current) {
        setPreview(result);
        requestKey.current = crypto.randomUUID();
      }
    } catch (e) {
      if (active.current) setError(message(e));
    } finally {
      if (active.current) setBusy(false);
    }
  }
  async function ask() {
    if (!preview) return;
    setBusy(true);
    setError("");
    setStreamNote("");
    request.current = new AbortController();
    try {
      const turn = await api<Turn>(endpoint, {
        ...send("POST", {
          question,
          preview_hash: preview.preview_hash,
          idempotency_key: requestKey.current,
        }),
        signal: request.current.signal,
      });
      if (!active.current) return;
      setTurns((previous) => [
        ...previous.filter((t) => t.id !== turn.id),
        turn,
      ]);
      setPreview(null);
      setQuestion("");
      const client = new HttpAgent({
        url: `/api${endpoint}/${turn.id}/stream`,
        threadId: runId,
        headers: { "X-Inkloom-CSRF": "1" },
      });
      agent.current = client;
      try {
        await client.runAgent({ runId: turn.id });
      } catch {
        if (active.current)
          setStreamNote(
            "Stream interrupted. Showing the validated saved answer.",
          );
      }
    } catch (e) {
      if (active.current) setError(message(e));
    } finally {
      if (active.current) setBusy(false);
    }
  }
  return (
    <details className="document-chat panel" ref={details} id="document-chat">
      <summary>Ask about this document</summary>
      <p>
        Understand the saved review’s flags and ask follow-up questions with
        source evidence.
      </p>
      <p className="muted">
        Questions and selected review excerpts go to your configured AI provider
        and are saved privately. Inspect the payload before sending. Only the
        last six completed turns are supplied to AI.
      </p>
      {disabled && (
        <Notice>
          Save changes and run a fresh check to discuss the current document.
        </Notice>
      )}
      <div className="form-actions chat-shortcuts">
        {[
          "Why was this document flagged?",
          "Which issues need attention first?",
          "What should I change?",
        ].map((q) => (
          <button
            key={q}
            className="button secondary compact"
            disabled={disabled || busy}
            onClick={() => void inspect(q)}
          >
            {q}
          </button>
        ))}
      </div>
      <div
        className="chat-history"
        aria-live="polite"
        aria-busy={busy}
        role="region"
        aria-label="Document conversation"
        tabIndex={0}
      >
        {loading && <p>Loading your private conversation…</p>}
        {earlier && <p className="muted">Showing the latest 30 questions.</p>}
        {!loading && !turns.length && (
          <p className="muted">
            Start with “Why was this document flagged?” or ask about a specific
            issue.
          </p>
        )}
        {turns.map((turn) => (
          <article key={turn.id} className="chat-turn">
            <h3>{turn.question}</h3>
            {turn.state === "pending" && (
              <Notice>
                This request has no saved answer yet. Refresh history; if it was
                interrupted, inspect and send a new question.
              </Notice>
            )}
            {turn.error && <Notice kind="error">{turn.error}</Notice>}
            {turn.message && <p>{turn.message}</p>}
            {turn.items?.map((item) => (
              <div className="chat-explanation" key={item.finding_id}>
                <div>
                  <Badge>{item.status.replaceAll("_", " ")}</Badge>
                  {item.dismissed && <Badge>Dismissed observation</Badge>}
                </div>
                <blockquote>{item.quote}</blockquote>
                <p>{item.explanation}</p>
                <details>
                  <summary>Stored finding reason</summary>
                  <p>{item.reason}</p>
                </details>
                {item.evidence_missing && (
                  <p className="muted">
                    No verified supporting source. This remains unverified and
                    needs human assessment.
                  </p>
                )}
                {item.citations.map((citation, i) => (
                  <details className="evidence" key={citation.id}>
                    <summary>
                      [{i + 1}] {citation.rule_key.replaceAll("_", " ")}
                    </summary>
                    <blockquote>{citation.excerpt}</blockquote>
                    <small>{citation.location}</small>
                    {citation.source_document_id && (
                      <p>
                        <a
                          target="_blank"
                          rel="noreferrer"
                          href={`/api${base}/sources/${citation.source_document_id}/download`}
                        >
                          Open cited source
                        </a>
                      </p>
                    )}
                  </details>
                ))}
              </div>
            ))}
            {turn.notice && <small>{turn.notice}</small>}
            {turn.metadata && (
              <p className="muted">
                Model: {turn.metadata.model || "not returned"} · Provider:{" "}
                {turn.metadata.provider || "not returned"}
              </p>
            )}
          </article>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void inspect(question);
        }}
      >
        <label>
          Question about this document
          <textarea
            maxLength={500}
            rows={2}
            value={question}
            disabled={busy || disabled}
            onChange={(e) => {
              setQuestion(e.target.value);
              setPreview(null);
            }}
            placeholder="Why was this flagged, and which approved rule applies?"
          />
        </label>
        <div className="form-actions">
          <button
            className="button secondary compact"
            disabled={disabled || busy || !question.trim()}
            type="submit"
          >
            Inspect question
          </button>
          <button
            className="button ghost compact"
            disabled={busy || disabled}
            type="button"
            onClick={() => {
              setError("");
              void loadHistory().catch((e) => setError(message(e)));
            }}
          >
            Refresh history
          </button>
        </div>
      </form>
      {preview && !disabled && (
        <section className="chat-preview">
          <h3>Review chat payload</h3>
          <p>
            {preview.redacted_values} values redacted. Check for confidential
            information that pattern redaction may miss.
          </p>
          <details>
            <summary>Inspect outbound question and review excerpts</summary>
            <pre>{JSON.stringify(preview.payload, null, 2)}</pre>
          </details>
          <button
            className="button primary compact"
            disabled={busy}
            onClick={() => void ask()}
          >
            Send question to AI
          </button>
        </section>
      )}
      {busy && <p role="status">Preparing explanation…</p>}
      {error && (
        <Notice kind="error">
          {error} Inspect again for a new request, or refresh history to recover
          an answer.
        </Notice>
      )}
      {streamNote && <Notice>{streamNote}</Notice>}
    </details>
  );
}
