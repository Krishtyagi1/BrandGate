ALTER TABLE structured_rules ADD COLUMN IF NOT EXISTS fact jsonb;
CREATE TABLE drafts (
 id uuid PRIMARY KEY, org_id uuid NOT NULL REFERENCES organisations(id), creator_id uuid NOT NULL REFERENCES users(id),
 title text NOT NULL, channel text NOT NULL, format text NOT NULL DEFAULT 'text', current_version_id uuid,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','pending_approval','approved','needs_changes','rejected')),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(org_id,id)
);
CREATE TABLE draft_versions (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, draft_id uuid NOT NULL, revision integer NOT NULL,
 author_id uuid NOT NULL REFERENCES users(id), text text NOT NULL, artifact_sha256 text NOT NULL,
 file_sha256 text, private_path text, filename text, projection jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(org_id,id), UNIQUE(org_id,draft_id,id), UNIQUE(org_id,draft_id,revision),
 FOREIGN KEY(org_id,draft_id) REFERENCES drafts(org_id,id)
);
ALTER TABLE drafts ADD CONSTRAINT current_version_same_draft FOREIGN KEY(org_id,id,current_version_id) REFERENCES draft_versions(org_id,draft_id,id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE ai_processing_consents (
 org_id uuid PRIMARY KEY REFERENCES organisations(id), approved_by uuid NOT NULL REFERENCES users(id),
 policy_version text NOT NULL, enabled boolean NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE review_runs (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, draft_id uuid NOT NULL, version_id uuid NOT NULL, guideline_version_id uuid NOT NULL,
 actor_id uuid NOT NULL REFERENCES users(id), idempotency_key text NOT NULL, run_kind text NOT NULL DEFAULT 'review',
 status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','completed','incomplete','failed','cancelled','interrupted')),
 step text NOT NULL DEFAULT 'Queued', result jsonb NOT NULL DEFAULT '{}', error text,
 created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, UNIQUE(org_id,id),
 UNIQUE(org_id,actor_id,run_kind,idempotency_key), FOREIGN KEY(org_id,draft_id,version_id) REFERENCES draft_versions(org_id,draft_id,id),
 FOREIGN KEY(org_id,guideline_version_id) REFERENCES guideline_versions(org_id,id)
);
CREATE TABLE review_events (
 org_id uuid NOT NULL, run_id uuid NOT NULL, sequence integer NOT NULL, event jsonb NOT NULL,
 PRIMARY KEY(org_id,run_id,sequence), FOREIGN KEY(org_id,run_id) REFERENCES review_runs(org_id,id)
);
CREATE TABLE ai_request_usage (
 id uuid PRIMARY KEY, org_id uuid NOT NULL REFERENCES organisations(id), actor_id uuid NOT NULL REFERENCES users(id),
 model text NOT NULL, purpose text NOT NULL, status text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE approval_requests (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, draft_id uuid NOT NULL, version_id uuid NOT NULL, run_id uuid NOT NULL,
 submitted_by uuid NOT NULL REFERENCES users(id), reviewer_id uuid NOT NULL REFERENCES users(id),
 status text NOT NULL DEFAULT 'pending', idempotency_key text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(org_id,id), UNIQUE(org_id,submitted_by,idempotency_key),
 FOREIGN KEY(org_id,draft_id,version_id) REFERENCES draft_versions(org_id,draft_id,id), FOREIGN KEY(org_id,run_id) REFERENCES review_runs(org_id,id)
);
CREATE UNIQUE INDEX one_pending_approval ON approval_requests(org_id,draft_id) WHERE status='pending';
CREATE TABLE approval_decisions (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, request_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES users(id),
 decision text NOT NULL, comment text NOT NULL, artifact_sha256 text NOT NULL, manual_visual_ack boolean NOT NULL,
 coverage jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(org_id,request_id),
 FOREIGN KEY(org_id,request_id) REFERENCES approval_requests(org_id,id)
);
CREATE TABLE review_comments (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, draft_id uuid NOT NULL, version_id uuid NOT NULL,
 actor_id uuid NOT NULL REFERENCES users(id), body text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(org_id,draft_id,version_id) REFERENCES draft_versions(org_id,draft_id,id)
);
CREATE TABLE brand_assets (
 id uuid PRIMARY KEY, org_id uuid NOT NULL REFERENCES organisations(id), actor_id uuid NOT NULL REFERENCES users(id),
 label text NOT NULL, private_path text NOT NULL, sha256 text NOT NULL, media_type text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(org_id,id)
);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['drafts','draft_versions','ai_processing_consents','review_runs','review_events','ai_request_usage','approval_requests','approval_decisions','review_comments','brand_assets'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_access ON %I USING (org_id::text=current_setting(''app.org_id'',true)) WITH CHECK (org_id::text=current_setting(''app.org_id'',true))',t);
  EXECUTE format('GRANT SELECT,INSERT ON %I TO inkloom_app',t);
 END LOOP;
 FOREACH t IN ARRAY ARRAY['draft_versions','review_events','approval_decisions','review_comments'] LOOP
  EXECUTE format('CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION block_audit_mutation()',t);
 END LOOP;
END $$;
GRANT UPDATE ON drafts,review_runs,approval_requests,ai_processing_consents,ai_request_usage TO inkloom_app;
