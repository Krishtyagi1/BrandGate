ALTER TABLE drafts ADD COLUMN campaign text NOT NULL DEFAULT '' CHECK (length(campaign)<=120);
CREATE TABLE finding_followups (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, run_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES users(id),
 finding_id text NOT NULL, question text NOT NULL CHECK(length(question)<=500), answer jsonb NOT NULL,
 idempotency_key text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(org_id,id), UNIQUE(org_id,actor_id,idempotency_key), FOREIGN KEY(org_id,run_id) REFERENCES review_runs(org_id,id)
);
CREATE TABLE visual_confirmations (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, run_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES users(id),
 finding_id text NOT NULL, verdict text NOT NULL CHECK(verdict IN ('confirmed','not_an_issue','uncertain')),
 note text NOT NULL CHECK(length(note) BETWEEN 1 AND 1000), created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(org_id,id), FOREIGN KEY(org_id,run_id) REFERENCES review_runs(org_id,id)
);
CREATE INDEX followups_period ON finding_followups(org_id,created_at);
CREATE INDEX reviews_latest_draft ON review_runs(org_id,draft_id,created_at DESC) WHERE run_kind='review';
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['finding_followups','visual_confirmations'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_access ON %I USING (org_id::text=current_setting(''app.org_id'',true)) WITH CHECK (org_id::text=current_setting(''app.org_id'',true))',t);
  EXECUTE format('GRANT SELECT,INSERT ON %I TO inkloom_app',t);
  EXECUTE format('CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION block_audit_mutation()',t);
 END LOOP;
END $$;
