export interface Coverage {
  text_complete: boolean;
  unsupported: string[];
  exclusions: string[];
  parts: string[];
}
export interface Anchor {
  part: string;
  block_id: string;
  start: number;
  end: number;
  quote: string;
}
export interface DraftVersion {
  id: string;
  draft_id: string;
  revision: number;
  author_id: string;
  text: string;
  artifact_sha256: string;
  file_sha256: string | null;
  filename: string | null;
  projection: {
    coverage: Coverage;
    blocks: Anchor[];
    unresolved_changes: number;
    image?: {
      ocr_status: string;
      ocr_engine: string | null;
      language: string | null;
      width: number;
      height: number;
    };
  };
  created_at: string;
}
export interface Evidence {
  id: string;
  type: string;
  rule_key: string;
  value: string;
  excerpt: string;
  location: string;
  source_document_id: string | null;
  source_download_url?: string | null;
  reference_url?: string | null;
  media_type?: string | null;
}
export interface Finding {
  id: string;
  category: string;
  severity: string;
  status: string;
  quote: string;
  start: number;
  end: number;
  reason: string;
  evidence: Evidence[];
  origin: string;
  dismissed: boolean;
  evidence_validation?: string;
}
export interface RewriteOption {
  id: string;
  label: string;
  text: string;
  original: string;
  start: number;
  end: number;
  length_note: string;
}
export interface ReviewRun {
  id: string;
  draft_id: string;
  version_id: string;
  guideline_version_id: string;
  status: string;
  step: string;
  run_kind: string;
  error: string | null;
  stale?: boolean;
  created_at: string;
  result: {
    findings?: Finding[];
    coverage?: Coverage;
    checks?: string[];
    metadata?: { model?: string; provider?: string; requested_model?: string };
    mode?: string;
    options?: RewriteOption[];
    validation_dropped?: number;
    check_coverage?: { check: string; status: string; reason?: string }[];
  };
}
export interface ApprovalRequest {
  id: string;
  draft_id: string;
  version_id: string;
  reviewer_id: string;
  reviewer_name: string;
  status: string;
  created_at: string;
  title?: string;
  creator_name?: string;
}
export interface Draft {
  id: string;
  title: string;
  channel: string;
  category?: string;
  platform?: string | null;
  requested_checks?: string[];
  task_instructions?: string;
  format: string;
  creator_id: string;
  creator_name?: string;
  current_version_id: string;
  status: string;
  updated_at: string;
  current_version: DraftVersion;
  versions: DraftVersion[];
  runs: ReviewRun[];
  comments: {
    id: string;
    body: string;
    actor_name: string;
    created_at: string;
    version_id: string;
  }[];
  approval_requests: ApprovalRequest[];
  decisions: {
    id: string;
    decision: string;
    comment: string;
    actor_name: string;
    created_at: string;
    artifact_sha256: string;
  }[];
}
export interface AiPreview {
  payload: Record<string, unknown>;
  preview_hash: string;
  redacted_values: number;
  guideline_version: number;
  policy_version: string;
  notice: string;
  visual_images?: { label: string; url: string }[];
}
export interface AiStatus {
  configured: boolean;
  model: string;
  policy_version: string;
  consent: { enabled: boolean; policy_version: string } | null;
  privacy_note: string;
  synthetic_connection_test: {
    status: string;
    reason?: string;
    model?: string;
  } | null;
  usage: { status: string; count: number }[];
}
