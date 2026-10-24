CREATE TABLE tutorial_states (
 user_id uuid PRIMARY KEY REFERENCES users(id), completed boolean NOT NULL DEFAULT false,
 dismissed boolean NOT NULL DEFAULT false, example_org_id uuid REFERENCES organisations(id),
 example_draft_id uuid, example_version_id uuid, updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE tutorial_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE tutorial_states FORCE ROW LEVEL SECURITY;
CREATE POLICY self_access ON tutorial_states USING(user_id::text=current_setting('app.user_id',true)) WITH CHECK(user_id::text=current_setting('app.user_id',true));
GRANT SELECT,INSERT,UPDATE ON tutorial_states TO inkloom_app;
UPDATE review_runs r SET review_scope=jsonb_build_object(
 'category',d.category,'platform',d.platform,'channel',d.channel,
 'requested_checks',CASE WHEN jsonb_array_length(d.requested_checks)>0 THEN d.requested_checks ELSE s.checks END,
 'task_instructions',d.task_instructions)
FROM drafts d,knowledge_snapshots s WHERE r.org_id=d.org_id AND r.draft_id=d.id
 AND s.org_id=r.org_id AND s.id=r.knowledge_snapshot_id AND r.review_scope='{}'::jsonb;
