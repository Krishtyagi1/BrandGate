export type Role = "owner" | "creator" | "reviewer";
export interface User {
  id: string;
  name: string;
  email: string;
}
export interface Organisation {
  id: string;
  name: string;
  role: Role;
  owner_id: string;
}
export interface Member {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: Role;
  status: "active" | "disabled";
}
export interface Version {
  id: string;
  version: number;
  status: "draft" | "active" | "archived";
  activated_at: string | null;
  created_at: string;
  rule_count: number;
}
export interface Source {
  id: string;
  filename: string;
  extraction_status: string;
  locations: { location: string; text: string }[];
}
export type RuleType =
  | "approved_fact"
  | "product_name"
  | "prohibited_term"
  | "required_disclaimer"
  | "tone"
  | "channel_instruction";
export interface Rule {
  id: string;
  type: RuleType;
  rule_key: string;
  value: string;
  scope_channel: string;
  source_document_id: string | null;
  source_excerpt: string | null;
  source_location: string | null;
  approved_by: string | null;
  revision: number;
  fact?: {
    kind: "price";
    entity: string;
    amount: string;
    currency: "INR" | "USD" | "EUR" | "GBP";
    unit: string;
    effective_from: string;
    effective_to: string | null;
  } | null;
}
export interface VersionDetail extends Version {
  rules: Rule[];
  sources: Source[];
}
export interface AuditEvent {
  id: string;
  action: string;
  actor_name: string;
  created_at: string;
  target_type: string;
  metadata: Record<string, unknown>;
}
