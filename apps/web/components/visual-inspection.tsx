"use client";
import { useEffect, useState } from "react";
import type { Finding } from "../../../packages/contracts/reviews";
import { api, message, send } from "@/lib/api";
import { Notice } from "./ui";

interface Point {
  x: number;
  y: number;
}
interface Contrast {
  ratio: number;
  foreground: string;
  background: string;
  notice: string;
  normal_text_threshold_met: boolean;
  large_text_threshold_met: boolean;
}
export default function VisualInspection({
  base,
  draftId,
  versionId,
  findings,
}: {
  base: string;
  draftId: string;
  versionId: string;
  findings: Finding[];
}) {
  const [foreground, setForeground] = useState<Point>({ x: 0, y: 0 });
  const [background, setBackground] = useState<Point>({ x: 0.5, y: 0.5 });
  const [target, setTarget] = useState("foreground");
  const [result, setResult] = useState<Contrast | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [references, setReferences] = useState<
    {
      id: string;
      label: string;
      excerpt: string;
      location: string;
      url: string;
    }[]
  >([]);
  const [referenceError, setReferenceError] = useState("");
  useEffect(() => {
    let active = true;
    api<{ references: typeof references }>(
      `${base}/drafts/${draftId}/visual-references`,
    )
      .then((result) => {
        if (active) setReferences(result.references);
      })
      .catch((e) => {
        if (active) setReferenceError(message(e));
      });
    return () => {
      active = false;
    };
  }, [base, draftId, versionId]);
  return (
    <figure className="visual-inspection">
      <div className="visual-stage">
        <img
          src={`/api${base}/drafts/${draftId}/versions/${versionId}/download`}
          alt="Original uploaded content. Click to select a contrast sample; coordinate inputs are available below."
          onClick={(e) => {
            const r = e.currentTarget.getBoundingClientRect();
            const point = {
              x: Math.min(
                0.999999,
                Math.max(0, (e.clientX - r.left) / r.width),
              ),
              y: Math.min(
                0.999999,
                Math.max(0, (e.clientY - r.top) / r.height),
              ),
            };
            (target === "foreground" ? setForeground : setBackground)(point);
            setResult(null);
          }}
        />
        {findings
          .filter((f) => f.region)
          .map((f, i) => (
            <span
              className="visual-region"
              key={f.id}
              title={`Advisory ${i + 1}: ${f.reason}`}
              style={{
                left: `${f.region!.x * 100}%`,
                top: `${f.region!.y * 100}%`,
                width: `${f.region!.width * 100}%`,
                height: `${f.region!.height * 100}%`,
              }}
            >
              <span>{i + 1}</span>
            </span>
          ))}
      </div>
      <figcaption>
        Original image. Outlined areas are advisory observations; a person must
        compare them with the approved references.
      </figcaption>
      <details className="manual-visual-fallback">
        <summary>Compare with current approved references</summary>
        <p>
          Manual fallback when vision is unavailable. Compare the symbol,
          placement and proportions. These are current owner-confirmed sources;
          an older review may use a different snapshot.
        </p>
        {referenceError && <Notice kind="error">{referenceError}</Notice>}
        {references.length
          ? references.map((ref) => (
              <figure key={ref.id}>
                <img src={ref.url} alt={ref.label} />
                <figcaption>
                  <strong>{ref.label}</strong>
                  <p>{ref.excerpt}</p>
                  <small>{ref.location}</small>
                  <p>
                    <a href={ref.url} target="_blank" rel="noreferrer">
                      Open approved reference
                    </a>
                  </p>
                </figcaption>
              </figure>
            ))
          : !referenceError && (
              <p>
                No confirmed logo images available. Ask an owner to add and
                confirm references in Rules.
              </p>
            )}
        <p>
          A separate reviewer must inspect the artwork before approving. No
          automated visual pass is implied.
        </p>
      </details>
      <details>
        <summary>Measure sampled colour contrast</summary>
        <p>
          Choose opaque foreground and background pixels. Click the image or
          enter coordinates as percentages. Gradients and anti-aliased edges
          need human inspection.
        </p>
        <label>
          Next click selects
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="foreground">Foreground</option>
            <option value="background">Background</option>
          </select>
        </label>
        <div className="contrast-coordinates">
          {(
            [
              ["Foreground", foreground, setForeground],
              ["Background", background, setBackground],
            ] as const
          ).map(([label, point, setPoint]) => (
            <fieldset key={label}>
              <legend>{label}</legend>
              {(["x", "y"] as const).map((axis) => (
                <label key={axis}>
                  {axis.toUpperCase()} %
                  <input
                    type="number"
                    min={0}
                    max={99.9999}
                    step="any"
                    value={Number((point[axis] * 100).toFixed(4))}
                    onChange={(e) => {
                      setPoint({
                        ...point,
                        [axis]: Math.min(
                          0.999999,
                          Math.max(0, Number(e.target.value) / 100),
                        ),
                      });
                      setResult(null);
                    }}
                  />
                </label>
              ))}
            </fieldset>
          ))}
        </div>
        <button
          className="button secondary compact"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              setResult(
                await api<Contrast>(
                  `${base}/drafts/${draftId}/contrast`,
                  send("POST", {
                    version_id: versionId,
                    foreground,
                    background,
                  }),
                ),
              );
            } catch (e) {
              setError(message(e));
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "Measuring…" : "Measure contrast"}
        </button>
        {error && <Notice kind="error">{error}</Notice>}
        {result && (
          <div aria-live="polite">
            <strong>Sample ratio {result.ratio.toFixed(2)}:1</strong>
            <p>
              {result.foreground} on {result.background}. Normal-text 4.5:1
              threshold: {result.normal_text_threshold_met ? "met" : "not met"};
              large-text 3:1 threshold:{" "}
              {result.large_text_threshold_met ? "met" : "not met"}. Threshold
              comparison uses the unrounded ratio.
            </p>
            <small>{result.notice}</small>
            <p>
              <a
                href="https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html"
                target="_blank"
                rel="noreferrer"
              >
                Contrast calculation reference
              </a>
            </p>
          </div>
        )}
      </details>
    </figure>
  );
}
