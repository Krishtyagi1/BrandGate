"use client";
import { useEffect, useState } from "react";
import type { Organisation } from "../../../packages/contracts";
import type { AiStatus } from "../../../packages/contracts/reviews";
import { api, message, send } from "@/lib/api";
import { Badge, Notice } from "./ui";

export default function AiSettings({ org }: { org: Organisation }) {
  const [data, setData] = useState<AiStatus | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [confirmed, setConfirmed] = useState(false);
  const base = `/organisations/${org.id}/ai`;
  useEffect(() => {
    api<AiStatus>(`${base}/status`)
      .then(setData)
      .catch((e) => setError(message(e)));
  }, [base]);
  async function change(enabled: boolean) {
    setBusy(true);
    setError("");
    try {
      await api(
        `${base}/consent`,
        send("POST", { enabled, policy_version: data!.policy_version }),
      );
      setData(await api<AiStatus>(`${base}/status`));
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel settings-section">
      <div className="section-heading">
        <h2>AI processing & privacy</h2>
        <Badge variant={data?.configured ? "success" : "warning"}>
          {data?.configured ? "Key configured" : "Key needed"}
        </Badge>
      </div>
      {error && <Notice kind="error">{error}</Notice>}
      <p>
        Documents are stored locally. AI reviews may send a redacted text
        extract, selected approved rules, and explicitly previewed original
        images to OpenRouter and its model provider.
      </p>
      <p className="muted">
        Free routes must meet zero pricing, no data collection and zero data
        retention settings. These controls do not guarantee confidentiality.
        Redaction can miss business secrets; inspect the outbound preview before
        every review. Image pixels cannot be redacted: inspect candidate and
        reference images before sending them.
      </p>
      {data && (
        <>
          <p>
            <strong>Connection check: </strong>
            {data.synthetic_connection_test?.status === "passed"
              ? `Passed · ${data.synthetic_connection_test.model}`
              : data.synthetic_connection_test?.reason || "Not tested"}
            .
          </p>
          <p>
            <strong>Processing:</strong>{" "}
            {data.consent?.enabled ? "Enabled by the owner" : "Disabled"}. Model
            selection: <code>{data.model}</code>
          </p>
          {org.role === "owner" &&
            (data.consent?.enabled ? (
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => change(false)}
              >
                Disable external AI
              </button>
            ) : (
              <>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={confirmed}
                    onChange={(e) => setConfirmed(e.target.checked)}
                  />
                  I am authorised to permit this external processing for this
                  organisation, and will review outbound payloads.
                </label>
                <button
                  className="button primary"
                  disabled={busy || !confirmed}
                  onClick={() => change(true)}
                >
                  Enable protected free AI
                </button>
              </>
            ))}
          <small className="ai-policy-id">
            Policy: {data.policy_version}. Keys stay on the backend.
          </small>
        </>
      )}
    </section>
  );
}
