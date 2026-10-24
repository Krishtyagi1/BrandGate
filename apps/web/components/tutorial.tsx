"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { X, HelpCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { api, message, send } from "@/lib/api";
import { Notice } from "./ui";
export default function Tutorial({
  onExample,
}: {
  onExample: () => Promise<unknown>;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [example, setExample] = useState<{
    org_id: string;
    draft_id: string;
    version_id: string;
    image_draft_id?: string;
  } | null>(null);
  useEffect(() => {
    api<{
      completed: boolean;
      dismissed: boolean;
      example?: { org_id: string; draft_id: string; version_id: string } | null;
    }>("/tutorial")
      .then((s) => {
        setOpen(!s.completed && !s.dismissed);
        setExample(s.example || null);
      })
      .catch(() => {});
  }, []);
  async function close(completed = false) {
    setError("");
    try {
      await api(
        "/tutorial",
        send("POST", completed ? { completed: true } : { dismissed: true }),
      );
      setOpen(false);
    } catch (e) {
      setError(message(e));
    }
  }
  async function start() {
    setBusy(true);
    setError("");
    try {
      const data = await api<{
        org_id: string;
        draft_id: string;
        version_id: string;
        image_draft_id?: string;
      }>("/tutorial/example", send("POST"));
      await onExample();
      setExample(data);
      router.push(`/org/${data.org_id}/brand`);
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button
        type="button"
        className="button ghost compact"
        onClick={() => setOpen(!open)}
      >
        <HelpCircle size={16} />
        Help
      </button>
      {open && (
        <section className="tutorial-panel" aria-label="Getting started">
          <button
            className="icon-button tutorial-close"
            aria-label="Dismiss welcome tutorial"
            disabled={busy}
            onClick={() => void close()}
          >
            <X size={18} />
          </button>
          <h2>
            {example ? "Follow the example" : "Welcome to Brand Content Review"}
          </h2>
          <p>
            Start with company rules, check your content, then send the saved
            revision to another person for approval.
          </p>
          <ol>
            <li>
              <strong>Rules:</strong> choose checks, add sources and confirm the
              proposed facts.
            </li>
            <li>
              <strong>New review:</strong> paste text or upload a document or
              image. Inspect the payload before using external AI.
            </li>
            <li>
              <strong>Tracking:</strong> find saved work, comments and assigned
              approvals. Edits always need a fresh check.
            </li>
          </ol>
          <p className="muted">
            Try Northstar Botanics, a fictional company in its own isolated
            example workspace. Its deliberately incorrect draft has no
            precomputed AI results. Creating the example does not enable
            external AI processing.
          </p>
          {error && <Notice kind="error">{error}</Notice>}
          {example ? (
            <div className="tutorial-links">
              <Link
                className="button secondary"
                href={`/org/${example.org_id}/brand`}
              >
                1. Confirm example rules
              </Link>
              <Link
                className="button secondary"
                href={`/org/${example.org_id}/reviews/${example.draft_id}`}
              >
                2. Open example draft
              </Link>
              <Link
                className="button secondary"
                href={`/org/${example.org_id}/content`}
              >
                3. See Tracking
              </Link>
              {example.image_draft_id && (
                <Link
                  className="button secondary"
                  href={`/org/${example.org_id}/reviews/${example.image_draft_id}`}
                >
                  Inspect example ad
                </Link>
              )}
            </div>
          ) : (
            <button
              className="button primary"
              disabled={busy}
              onClick={() => void start()}
            >
              {busy ? "Preparing example…" : "Try the fictional example"}
            </button>
          )}
          <div className="form-actions">
            <button
              className="button ghost compact"
              disabled={busy}
              onClick={() => void close(true)}
            >
              Got it
            </button>
            <button
              className="button ghost compact"
              disabled={busy}
              onClick={() => void close()}
            >
              Dismiss for now
            </button>
            <small>Replay this guide from Help.</small>
          </div>
        </section>
      )}
    </>
  );
}
