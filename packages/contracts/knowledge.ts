export const CHECKS = [
  [
    "prices",
    "Products & prices",
    "Compare product names and prices with approved company facts.",
  ],
  [
    "claims",
    "Claims & facts",
    "Check factual promises and claims against approved evidence.",
  ],
  [
    "tone",
    "Tone",
    "Compare writing with your company’s approved voice guidance.",
  ],
  [
    "language",
    "Language & terminology",
    "Check preferred names, terms and prohibited wording.",
  ],
  [
    "required_wording",
    "Required wording",
    "Look for required disclaimers and phrases.",
  ],
  [
    "colours_fonts",
    "Colours & fonts",
    "Compare supported visual colours with approved references. Font identity may need human review.",
  ],
  [
    "logos",
    "Logos & visual examples",
    "Compare static images with approved visual references when supported.",
  ],
  [
    "accessibility",
    "Accessibility",
    "Run supported accessibility checks. This is not accessibility certification.",
  ],
] as const;
export const checkLabel = (check: string) =>
  CHECKS.find(([key]) => key === check)?.[1] || check.replaceAll("_", " ");
export interface CheckCoverage {
  check: string;
  status: string;
  reason?: string;
}
export interface KnowledgeSource {
  id: string;
  filename: string;
  media_type?: string;
  download_url?: string;
  extraction_status?: string;
  locations: { location: string; text: string }[];
}
export interface KnowledgeRule {
  id: string;
  type: string;
  rule_key: string;
  value: string;
  check?: string;
  scope_channel?: string;
  source_document_id?: string | null;
  source_excerpt?: string | null;
  source_location?: string | null;
  approved_by?: string | null;
  existing_rule_id?: string | null;
  status?: string;
  fact?: Record<string, unknown> | null;
}
export interface KnowledgeView {
  version: { id: string; version: number; status: string } | null;
  snapshot_id: string | null;
  checks: string[];
  instructions: string;
  sources: KnowledgeSource[];
  rules: KnowledgeRule[];
  proposals: KnowledgeRule[];
  coverage: CheckCoverage[];
  extraction: {
    status: string;
    error?: string | null;
    processed?: number;
    total?: number;
  };
}
