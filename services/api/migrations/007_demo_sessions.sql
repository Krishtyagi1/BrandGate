CREATE TABLE demo_sessions (
 token_hash text PRIMARY KEY REFERENCES sessions(token_hash) ON DELETE CASCADE,
 org_id uuid NOT NULL REFERENCES organisations(id)
);
GRANT SELECT,INSERT ON demo_sessions TO inkloom_app;
