"use client";
import { useId, useLayoutEffect, useRef, useState } from "react";
import { Info } from "lucide-react";
import { CHECKS, checkLabel } from "../../../packages/contracts/knowledge";
import type { CheckCoverage } from "../../../packages/contracts/knowledge";

export function InfoHelp({
  text,
  label = "More information",
}: {
  text: string;
  label?: string;
}) {
  const [open, setOpen] = useState(false),
    id = useId();
  const anchor = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState({ left: 8, top: 8 });
  useLayoutEffect(() => {
    if (!open) return;
    function place() {
      const rect = anchor.current?.getBoundingClientRect();
      if (!rect) return;
      const width = Math.min(250, window.innerWidth * 0.7);
      setPosition({
        left: Math.max(
          8,
          Math.min(rect.left - 110, window.innerWidth - width - 8),
        ),
        top: rect.bottom + 6,
      });
    }
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open]);
  return (
    <span
      className="info-help"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        ref={anchor}
        type="button"
        className="info-button"
        aria-label={label}
        aria-expanded={open}
        aria-describedby={open ? id : undefined}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={() => setOpen(true)}
        onKeyDown={(event) => {
          if (event.key === "Escape") setOpen(false);
        }}
      >
        <Info size={15} />
      </button>
      {open && (
        <span
          id={id}
          role="tooltip"
          className="info-tooltip"
          style={{ position: "fixed", ...position }}
        >
          {text}
        </span>
      )}
    </span>
  );
}
export function CheckOptions({
  value,
  onChange,
  disabled = false,
}: {
  value: string[];
  onChange: (value: string[]) => void;
  disabled?: boolean;
}) {
  return (
    <div className="check-options">
      {CHECKS.map(([key, title, help]) => (
        <div className="check-option" key={key}>
          <label className="checkbox-label">
            <input
              type="checkbox"
              disabled={disabled}
              checked={value.includes(key)}
              onChange={(e) =>
                onChange(
                  e.target.checked
                    ? [...value, key]
                    : value.filter((v) => v !== key),
                )
              }
            />
            {title}
          </label>
          <InfoHelp text={help} label={`About ${title}`} />
        </div>
      ))}
    </div>
  );
}
export function CoverageList({ rows }: { rows: CheckCoverage[] }) {
  if (!rows.length) return null;
  return (
    <ul className="check-coverage" aria-label="Check coverage">
      {rows.map((row) => (
        <li key={row.check}>
          <div>
            <strong>{checkLabel(row.check)}</strong>
            <span className="coverage-status">
              {(
                {
                  source_missing: "Source missing",
                  missing: "Source missing",
                  not_checked: "Not checked",
                  issues_found: "Issues found",
                  checked: "Checked",
                  passed: "Checked",
                  covered: "Source available",
                  available: "Source available",
                  supported: "Source available",
                  needs_confirmation: "Needs confirmation",
                  unsupported: "Unsupported",
                  unavailable: "Not checked",
                  incomplete: "Not checked",
                } as Record<string, string>
              )[row.status] || row.status.replaceAll("_", " ")}
            </span>
          </div>
          {row.reason && <p>{row.reason}</p>}
        </li>
      ))}
    </ul>
  );
}
