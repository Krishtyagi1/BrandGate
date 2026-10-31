-- Keep demo tokens out of the legacy session registry: old app rollbacks fail closed.
ALTER TABLE demo_sessions ADD COLUMN user_id uuid REFERENCES users(id);
ALTER TABLE demo_sessions ADD COLUMN expires_at timestamptz;
UPDATE demo_sessions d SET user_id=s.user_id, expires_at=s.expires_at
 FROM sessions s WHERE s.token_hash=d.token_hash;
ALTER TABLE demo_sessions ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE demo_sessions ALTER COLUMN expires_at SET NOT NULL;
ALTER TABLE demo_sessions DROP CONSTRAINT demo_sessions_token_hash_fkey;
DELETE FROM sessions WHERE token_hash IN (SELECT token_hash FROM demo_sessions);
GRANT DELETE ON demo_sessions TO inkloom_app;
