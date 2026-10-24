ALTER TABLE guideline_versions ADD COLUMN checks jsonb NOT NULL DEFAULT '["prices","claims","tone","language","required_wording","colours_fonts","logos","accessibility"]';
ALTER TABLE guideline_versions ADD COLUMN instructions text NOT NULL DEFAULT '';
ALTER TABLE source_documents ADD COLUMN media_type text NOT NULL DEFAULT 'application/octet-stream';
UPDATE source_documents SET media_type=CASE WHEN lower(filename) LIKE '%.pdf' THEN 'application/pdf' WHEN lower(filename) LIKE '%.docx' THEN 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ELSE media_type END;
CREATE TABLE knowledge_snapshots (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), org_id uuid NOT NULL, guideline_version_id uuid NOT NULL,
 sequence integer NOT NULL, checks jsonb NOT NULL, instructions text NOT NULL, rules jsonb NOT NULL, "references" jsonb NOT NULL DEFAULT '[]',
 approved_by uuid REFERENCES users(id), created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(org_id,id), UNIQUE(org_id,guideline_version_id,sequence),
 FOREIGN KEY(org_id,guideline_version_id) REFERENCES guideline_versions(org_id,id)
);
CREATE TABLE knowledge_proposals (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), org_id uuid NOT NULL, guideline_version_id uuid NOT NULL,
 type text NOT NULL, rule_key text NOT NULL, value text NOT NULL, check_name text NOT NULL, scope_channel text NOT NULL DEFAULT 'global',
 source_document_id uuid, source_excerpt text, source_location text, fact jsonb,
 existing_rule_id uuid, status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','confirmed','discarded')),
 method text NOT NULL CHECK(method IN ('company_entered','local_suggestion','ai')), confirmed_rule_id uuid,
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(org_id,guideline_version_id) REFERENCES guideline_versions(org_id,id),
 FOREIGN KEY(org_id,source_document_id) REFERENCES source_documents(org_id,id)
);
CREATE TABLE knowledge_extractions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), org_id uuid NOT NULL, guideline_version_id uuid NOT NULL,
 actor_id uuid NOT NULL REFERENCES users(id), status text NOT NULL, error text,
 processed integer NOT NULL DEFAULT 0, total integer NOT NULL DEFAULT 0, source_ids jsonb NOT NULL DEFAULT '[]',
 metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz,
 FOREIGN KEY(org_id,guideline_version_id) REFERENCES guideline_versions(org_id,id)
);
CREATE UNIQUE INDEX one_knowledge_job ON knowledge_extractions(org_id,guideline_version_id) WHERE status IN ('queued','running');
INSERT INTO knowledge_snapshots(org_id,guideline_version_id,sequence,checks,instructions,rules,approved_by)
 SELECT v.org_id,v.id,1,v.checks,v.instructions,coalesce((SELECT jsonb_agg(to_jsonb(r) ORDER BY r.created_at,r.id) FROM structured_rules r WHERE r.org_id=v.org_id AND r.guideline_version_id=v.id AND r.approved_by IS NOT NULL),'[]'::jsonb),v.approved_by
 FROM guideline_versions v WHERE v.status IN ('active','archived') OR EXISTS(SELECT 1 FROM review_runs x WHERE x.guideline_version_id=v.id);
ALTER TABLE review_runs ADD COLUMN knowledge_snapshot_id uuid;
ALTER TABLE review_runs ADD COLUMN review_scope jsonb NOT NULL DEFAULT '{}';
UPDATE review_runs r SET knowledge_snapshot_id=s.id FROM knowledge_snapshots s WHERE s.org_id=r.org_id AND s.guideline_version_id=r.guideline_version_id;
ALTER TABLE review_runs ADD CONSTRAINT review_snapshot_org FOREIGN KEY(org_id,knowledge_snapshot_id) REFERENCES knowledge_snapshots(org_id,id);
ALTER TABLE drafts ADD COLUMN category text NOT NULL DEFAULT 'other';
ALTER TABLE drafts ADD COLUMN platform text;
ALTER TABLE drafts ADD COLUMN requested_checks jsonb NOT NULL DEFAULT '[]';
ALTER TABLE drafts ADD COLUMN task_instructions text NOT NULL DEFAULT '';
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['knowledge_snapshots','knowledge_proposals','knowledge_extractions'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('CREATE POLICY tenant_access ON %I USING (org_id::text=current_setting(''app.org_id'',true)) WITH CHECK (org_id::text=current_setting(''app.org_id'',true))',t);
  EXECUTE format('GRANT SELECT,INSERT ON %I TO inkloom_app',t);
 END LOOP;
END $$;
CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON knowledge_snapshots FOR EACH ROW EXECUTE FUNCTION block_audit_mutation();
GRANT UPDATE ON knowledge_proposals,knowledge_extractions TO inkloom_app;
