CREATE TABLE IF NOT EXISTS users (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), email text NOT NULL UNIQUE, name text NOT NULL,
 password_hash text NOT NULL, verified boolean NOT NULL DEFAULT false, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS verification_tokens (
 token_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES users(id), expires_at timestamptz NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES users(id), expires_at timestamptz NOT NULL
);
CREATE TABLE IF NOT EXISTS organisations (
 id uuid PRIMARY KEY, name text NOT NULL CHECK(length(name) BETWEEN 1 AND 100), owner_id uuid NOT NULL REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS memberships (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), org_id uuid NOT NULL REFERENCES organisations(id), user_id uuid NOT NULL REFERENCES users(id),
 role text NOT NULL CHECK(role IN ('owner','creator','reviewer')), status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','disabled')),
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(org_id,user_id)
);
CREATE TABLE IF NOT EXISTS invitations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), org_id uuid NOT NULL REFERENCES organisations(id), email text NOT NULL,
 role text NOT NULL CHECK(role IN ('creator','reviewer')), token_hash text NOT NULL UNIQUE, invited_by uuid NOT NULL REFERENCES users(id),
 expires_at timestamptz NOT NULL, accepted_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS guideline_versions (
 id uuid PRIMARY KEY, org_id uuid NOT NULL REFERENCES organisations(id), version integer NOT NULL,
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','archived')), approved_by uuid REFERENCES users(id),
 activated_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(org_id,version), UNIQUE(org_id,id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_version ON guideline_versions(org_id) WHERE status='active';
CREATE TABLE IF NOT EXISTS source_documents (
 id uuid PRIMARY KEY, org_id uuid NOT NULL, guideline_version_id uuid NOT NULL, filename text NOT NULL,
 private_path text NOT NULL, sha256 text NOT NULL, extraction_status text NOT NULL, extracted_text text NOT NULL,
 locations jsonb NOT NULL DEFAULT '[]', created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(org_id,id),
 FOREIGN KEY(org_id,guideline_version_id) REFERENCES guideline_versions(org_id,id)
);
CREATE TABLE IF NOT EXISTS structured_rules (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), org_id uuid NOT NULL, guideline_version_id uuid NOT NULL,
 type text NOT NULL CHECK(type IN ('approved_fact','product_name','prohibited_term','required_disclaimer','tone','channel_instruction')),
 rule_key text NOT NULL, value text NOT NULL, scope_channel text NOT NULL DEFAULT 'global',
 source_document_id uuid, source_excerpt text, source_location text, approved_by uuid REFERENCES users(id),
 revision integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(org_id,guideline_version_id) REFERENCES guideline_versions(org_id,id),
 FOREIGN KEY(org_id,source_document_id) REFERENCES source_documents(org_id,id)
);
CREATE TABLE IF NOT EXISTS audit_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), org_id uuid NOT NULL REFERENCES organisations(id), actor_id uuid NOT NULL REFERENCES users(id),
 action text NOT NULL, target_type text NOT NULL, target_id text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS diagnostic_runs (
 id uuid PRIMARY KEY, org_id uuid NOT NULL REFERENCES organisations(id), actor_id uuid NOT NULL REFERENCES users(id),
 thread_id uuid NOT NULL, status text NOT NULL CHECK(status IN ('running','completed','cancelled','failed','interrupted')),
 created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz
);
UPDATE diagnostic_runs SET status='interrupted',completed_at=now() WHERE status='running';
CREATE OR REPLACE FUNCTION block_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
 BEGIN RAISE EXCEPTION 'Audit events are append-only'; END; $$;
DROP TRIGGER IF EXISTS audit_immutable ON audit_events;
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION block_audit_mutation();

ALTER TABLE organisations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organisations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS org_access ON organisations;
CREATE POLICY org_access ON organisations USING (
 owner_id::text=current_setting('app.user_id',true)
 OR id::text=current_setting('app.org_id',true)
 OR EXISTS(SELECT 1 FROM memberships m WHERE m.org_id=organisations.id AND m.user_id::text=current_setting('app.user_id',true) AND m.status='active')
) WITH CHECK(owner_id::text=current_setting('app.user_id',true));

ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS membership_read ON memberships;
CREATE POLICY membership_read ON memberships FOR SELECT USING (user_id::text=current_setting('app.user_id',true) OR org_id::text=current_setting('app.org_id',true));
DROP POLICY IF EXISTS membership_write ON memberships;
CREATE POLICY membership_write ON memberships FOR INSERT WITH CHECK(org_id::text=current_setting('app.org_id',true));
DROP POLICY IF EXISTS membership_update ON memberships;
CREATE POLICY membership_update ON memberships FOR UPDATE USING(org_id::text=current_setting('app.org_id',true)) WITH CHECK(org_id::text=current_setting('app.org_id',true));

ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS invitation_read ON invitations;
CREATE POLICY invitation_read ON invitations FOR SELECT USING(org_id::text=current_setting('app.org_id',true) OR email=current_setting('app.email',true));
DROP POLICY IF EXISTS invitation_insert ON invitations;
CREATE POLICY invitation_insert ON invitations FOR INSERT WITH CHECK(org_id::text=current_setting('app.org_id',true));
DROP POLICY IF EXISTS invitation_update ON invitations;
CREATE POLICY invitation_update ON invitations FOR UPDATE USING(org_id::text=current_setting('app.org_id',true) OR email=current_setting('app.email',true));

DO $$ DECLARE table_name text; BEGIN
 FOREACH table_name IN ARRAY ARRAY['guideline_versions','source_documents','structured_rules','audit_events','diagnostic_runs'] LOOP
  EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',table_name);
  EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',table_name);
  EXECUTE format('DROP POLICY IF EXISTS tenant_access ON %I',table_name);
  EXECUTE format('CREATE POLICY tenant_access ON %I USING (org_id::text=current_setting(''app.org_id'',true)) WITH CHECK (org_id::text=current_setting(''app.org_id'',true))',table_name);
 END LOOP;
END $$;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO inkloom_app;
GRANT SELECT,INSERT,UPDATE,DELETE ON users,verification_tokens,sessions TO inkloom_app;
GRANT SELECT,INSERT,UPDATE ON organisations,memberships,invitations,guideline_versions,structured_rules TO inkloom_app;
GRANT SELECT,INSERT ON source_documents,audit_events TO inkloom_app;
GRANT SELECT,INSERT,UPDATE ON diagnostic_runs TO inkloom_app;
GRANT DELETE ON structured_rules TO inkloom_app;
