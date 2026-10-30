CREATE TABLE document_chat_requests (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, run_id uuid NOT NULL, actor_id uuid NOT NULL REFERENCES users(id),
 question text NOT NULL CHECK(length(question) BETWEEN 1 AND 500), preview_hash text NOT NULL,
 idempotency_key text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(org_id,id), UNIQUE(org_id,actor_id,idempotency_key),
 FOREIGN KEY(org_id,run_id) REFERENCES review_runs(org_id,id)
);
CREATE TABLE document_chat_answers (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, answer jsonb NOT NULL, error text,
 error_status integer, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(org_id,id) REFERENCES document_chat_requests(org_id,id)
);
CREATE INDEX document_chat_history ON document_chat_requests(org_id,run_id,actor_id,created_at,id);
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['document_chat_requests','document_chat_answers'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_access ON %I USING (org_id::text=current_setting(''app.org_id'',true)) WITH CHECK (org_id::text=current_setting(''app.org_id'',true))',t);
  EXECUTE format('GRANT SELECT,INSERT ON %I TO inkloom_app',t);
  EXECUTE format('CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION block_audit_mutation()',t);
 END LOOP;
END $$;
