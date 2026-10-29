"use client";
import { useState } from "react";
import { api, message, send } from "@/lib/api";
import { Notice } from "./ui";
export default function CampaignField({
  base,
  draftId,
  versionId,
  initial,
  editable,
}: {
  base: string;
  draftId: string;
  versionId: string;
  initial: string;
  editable: boolean;
}) {
  const [value, setValue] = useState(initial),
    [saved, setSaved] = useState(initial),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  if (!editable) return <p>Campaign: {initial || "No campaign"}</p>;
  return (
    <div className="campaign-field">
      <label>
        Campaign <span className="muted">(optional)</span>
        <input
          maxLength={120}
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      </label>
      <button
        className="button secondary compact"
        disabled={busy || value.trim() === saved}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            const result = await api<{ campaign: string }>(
              `${base}/drafts/${draftId}/campaign`,
              send("POST", {
                expected_current_version_id: versionId,
                campaign: value,
              }),
            );
            setValue(result.campaign);
            setSaved(result.campaign);
          } catch (e) {
            setError(message(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        Save campaign
      </button>
      {error && <Notice kind="error">{error}</Notice>}
    </div>
  );
}
