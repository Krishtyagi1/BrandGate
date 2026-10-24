"use client";
import { useState, type FormEvent } from "react";
import type { KnowledgeRule } from "../../../packages/contracts/knowledge";
import { CHECKS } from "../../../packages/contracts/knowledge";

const ruleTypes = [
  ["approved_fact", "Approved fact"],
  ["product_name", "Product name"],
  ["prohibited_term", "Prohibited term"],
  ["required_disclaimer", "Required wording"],
  ["tone", "Tone guidance"],
  ["channel_instruction", "Other guidance"],
] as const;
const defaultType = (check: string) =>
  check === "tone"
    ? "tone"
    : check === "language"
      ? "product_name"
      : check === "required_wording"
        ? "required_disclaimer"
        : ["prices", "claims"].includes(check)
          ? "approved_fact"
          : "channel_instruction";
export type ProposalFieldsValue = {
  type: string;
  rule_key: string;
  value: string;
  check: string;
  scope_channel: string;
  source_document_id: string | null;
  source_excerpt: string | null;
  source_location: string | null;
  approved: false;
  fact: Record<string, unknown> | null;
};
export default function ProposalFields({
  rule,
  busy,
  onSave,
  onCancel,
}: {
  rule?: KnowledgeRule;
  busy: boolean;
  onSave: (value: ProposalFieldsValue) => Promise<void>;
  onCancel?: () => void;
}) {
  const [check, setCheck] = useState(rule?.check || "claims"),
    [type, setType] = useState(rule?.type || "approved_fact");
  const [price, setPrice] = useState(rule?.fact?.kind === "price");
  const fact = rule?.fact;
  const sourceBacked = !!rule?.source_document_id;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await onSave({
      type,
      check,
      rule_key: String(data.get("rule_key") || ""),
      value: String(data.get("value") || ""),
      scope_channel: rule?.scope_channel || "global",
      approved: false,
      source_document_id: rule?.source_document_id || null,
      source_excerpt: rule?.source_excerpt || null,
      source_location: rule?.source_location || null,
      fact: price
        ? {
            kind: "price",
            entity: String(data.get("entity") || ""),
            amount: String(data.get("amount") || ""),
            currency: String(data.get("currency") || "INR"),
            unit: String(data.get("unit") || ""),
            effective_from: String(data.get("effective_from") || ""),
            effective_to: data.get("effective_to") || null,
          }
        : null,
    });
  }
  return (
    <form className="proposal-fields" onSubmit={submit}>
      <p className="muted">
        {sourceBacked
          ? "Source evidence is preserved. Changes to source-backed facts must still match the quoted source; unsupported changes will be rejected."
          : "Company-entered guidance. No uploaded source is claimed. Save it as a proposal, then review and confirm it below."}
      </p>
      <div className="form-pair">
        <label>
          Rule name
          <input
            name="rule_key"
            required
            maxLength={100}
            defaultValue={rule?.rule_key || ""}
            placeholder="For example: launch price or preferred voice"
          />
        </label>
        <label>
          Check category
          <select
            value={check}
            onChange={(event) => {
              setCheck(event.target.value);
              setType(defaultType(event.target.value));
            }}
          >
            {CHECKS.map(([key, label]) => (
              <option value={key} key={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label>
        Guidance or approved wording
        <textarea
          name="value"
          required
          maxLength={2000}
          rows={3}
          defaultValue={rule?.value || ""}
          placeholder="Enter the exact fact or guidance your company approves."
        />
      </label>
      <label>
        Rule type
        <select value={type} onChange={(event) => setType(event.target.value)}>
          {ruleTypes.map(([key, label]) => (
            <option value={key} key={key}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <details open={price}>
        <summary>
          Structured price fields <span className="muted">(optional)</span>
        </summary>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={price}
            onChange={(event) => {
              setPrice(event.target.checked);
              if (event.target.checked) {
                setType("approved_fact");
                setCheck("prices");
              }
            }}
          />
          Use exact product, price and effective dates
        </label>
        <fieldset disabled={!price}>
          <div className="form-pair">
            <label>
              Product
              <input
                name="entity"
                required={price}
                maxLength={150}
                defaultValue={String(fact?.entity || "")}
              />
            </label>
            <label>
              Amount
              <input
                name="amount"
                type="number"
                min="0"
                step="0.01"
                required={price}
                defaultValue={String(fact?.amount ?? "")}
              />
            </label>
          </div>
          <div className="form-pair">
            <label>
              Currency
              <select
                name="currency"
                defaultValue={String(fact?.currency || "INR")}
              >
                {["INR", "USD", "EUR", "GBP"].map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </label>
            <label>
              Unit
              <input
                name="unit"
                required={price}
                maxLength={80}
                defaultValue={String(fact?.unit || "")}
                placeholder="For example: per month"
              />
            </label>
          </div>
          <div className="form-pair">
            <label>
              Effective from
              <input
                name="effective_from"
                type="date"
                required={price}
                defaultValue={String(fact?.effective_from || "")}
              />
            </label>
            <label>
              Effective until <span className="muted">(optional)</span>
              <input
                name="effective_to"
                type="date"
                defaultValue={String(fact?.effective_to || "")}
              />
            </label>
          </div>
        </fieldset>
      </details>
      <div className="form-actions">
        <button className="button secondary" disabled={busy}>
          {busy
            ? "Saving…"
            : rule
              ? "Save proposed fields"
              : "Add proposed guidance"}
        </button>
        {onCancel && (
          <button
            className="button ghost"
            type="button"
            disabled={busy}
            onClick={onCancel}
          >
            Cancel edit
          </button>
        )}
      </div>
    </form>
  );
}
