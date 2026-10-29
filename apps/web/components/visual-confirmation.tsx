"use client";
import { useEffect, useState } from "react";
import { api, date, message, send } from "@/lib/api";
import { Notice } from "./ui";
interface Assessment {
  id: string;
  finding_id: string;
  verdict: string;
  note: string;
  actor_name: string;
  created_at: string;
}
export default function VisualConfirmation({
  base,
  runId,
  findingId,
  canConfirm,
  disabled,
}: {
  base: string;
  runId: string;
  findingId: string;
  canConfirm: boolean;
  disabled: boolean;
}) {
  const [items, setItems] = useState<Assessment[]>([]),
    [note, setNote] = useState(""),
    [verdict, setVerdict] = useState("uncertain"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const url = `${base}/review-runs/${runId}/visual-confirmations`;
  useEffect(() => {
    let active = true;
    api<Assessment[]>(url)
      .then((rows) => {
        if (active) setItems(rows);
      })
      .catch((e) => {
        if (active) setError(message(e));
      });
    return () => {
      active = false;
    };
  }, [url]);
  return (
    <details>
      <summary>Human visual assessment</summary>
      <p className="muted">
        A separate reviewer records a judgement. The original finding stays
        advisory; this does not approve the draft.
      </p>
      {items
        .filter((i) => i.finding_id === findingId)
        .map((i) => (
          <blockquote key={i.id}>
            <strong>{i.verdict.replaceAll("_", " ")}</strong>
            <p>{i.note}</p>
            <small>
              {i.actor_name} · {date(i.created_at)}
            </small>
          </blockquote>
        ))}
      {canConfirm && (
        <>
          <label>
            Assessment
            <select
              value={verdict}
              onChange={(e) => setVerdict(e.target.value)}
            >
              <option value="uncertain">Uncertain</option>
              <option value="confirmed">Confirmed issue</option>
              <option value="not_an_issue">Not an issue</option>
            </select>
          </label>
          <label>
            Comparison note
            <textarea
              rows={2}
              maxLength={1000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <button
            className="button secondary compact"
            disabled={disabled || busy || !note.trim()}
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                await api(
                  url,
                  send("POST", { finding_id: findingId, verdict, note }),
                );
                setItems(await api<Assessment[]>(url));
                setNote("");
              } catch (e) {
                setError(message(e));
              } finally {
                setBusy(false);
              }
            }}
          >
            Record assessment
          </button>
        </>
      )}
      {error && <Notice kind="error">{error}</Notice>}
    </details>
  );
}
