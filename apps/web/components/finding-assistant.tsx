"use client";
import { useEffect, useRef, useState } from "react";
import { HttpAgent } from "@ag-ui/client";
import type { Evidence } from "../../../packages/contracts/reviews";
import { api, message, send } from "@/lib/api";
import { Notice } from "./ui";

interface Answer {
  id: string;
  answer: string;
  covered: boolean;
  mode: string;
  citations: Evidence[];
}

export default function FindingAssistant({
  base,
  runId,
  findingId,
  disabled,
}: {
  base: string;
  runId: string;
  findingId: string;
  disabled: boolean;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const agent = useRef<HttpAgent | null>(null);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      agent.current?.abortRun();
    };
  }, []);
  async function ask(value: string) {
    setBusy(true);
    setError("");
    setAnswer(null);
    setText("");
    try {
      const result = await api<Answer>(
        `${base}/review-runs/${runId}/follow-up`,
        send("POST", {
          finding_id: findingId,
          question: value,
          idempotency_key: crypto.randomUUID(),
        }),
      );
      if (!alive.current) return;
      setAnswer(result);
      const client = new HttpAgent({
        url: `/api${base}/follow-ups/${result.id}/stream`,
        threadId: result.id,
        headers: { "X-Inkloom-CSRF": "1" },
      });
      agent.current = client;
      try {
        await client.runAgent(
          { runId: result.id },
          {
            onTextMessageContentEvent: ({ event }) => {
              if (alive.current) setText((previous) => previous + event.delta);
            },
          },
        );
      } catch {
        if (alive.current) {
          setText(result.answer);
          setError("Stream interrupted. Showing the saved answer.");
        }
      }
      if (alive.current) setText(result.answer);
    } catch (e) {
      if (alive.current) setError(message(e));
    } finally {
      if (alive.current) setBusy(false);
    }
  }
  return (
    <details className="finding-assistant">
      <summary>Ask about this finding</summary>
      <p className="muted">
        Read-only answers from this review’s approved excerpts. Questions are
        saved privately for guideline-gap insights. No external AI call.
      </p>
      <div className="form-actions">
        <button
          className="button secondary compact"
          disabled={disabled || busy}
          onClick={() => ask("Why was this flagged?")}
        >
          Why was this flagged?
        </button>
        <button
          className="button secondary compact"
          disabled={disabled || busy}
          onClick={() => ask("How can I fix it?")}
        >
          How can I fix it?
        </button>
      </div>
      <label>
        Your question
        <input
          maxLength={500}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about this finding"
        />
      </label>
      <button
        className="button ghost compact"
        disabled={disabled || busy || !question.trim()}
        onClick={() => ask(question)}
      >
        {busy ? "Reading approved guidance…" : "Ask"}
      </button>
      {disabled && (
        <p className="muted">
          Save changes and run a fresh check to ask about current findings.
        </p>
      )}
      {error && <Notice kind="error">{error}</Notice>}
      {answer && (
        <div className="assistant-answer" aria-live="polite">
          <strong>
            {answer.covered ? "Approved guidance" : "Evidence missing"}
          </strong>
          <p style={{ whiteSpace: "pre-wrap" }}>
            {text || "Loading saved answer…"}
          </p>
          {answer.citations.map((c, i) => (
            <details className="evidence" key={c.id}>
              <summary>
                [{i + 1}] {c.rule_key.replaceAll("_", " ")}
              </summary>
              <blockquote>{c.excerpt}</blockquote>
              <small>{c.location}</small>
              {c.source_document_id && (
                <p>
                  <a
                    href={`/api${base}/sources/${c.source_document_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open cited source
                  </a>
                </p>
              )}
            </details>
          ))}
        </div>
      )}
    </details>
  );
}
