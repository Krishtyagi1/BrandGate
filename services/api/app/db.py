from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from .config import ADMIN_URL, DATABASE_URL


def migrate():
    with psycopg.connect(ADMIN_URL, client_encoding="utf8") as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        for migration in sorted((Path(__file__).parents[1] / "migrations").glob("*.sql")):
            if not conn.execute(
                "SELECT 1 FROM schema_migrations WHERE name=%s", (migration.name,)
            ).fetchone():
                conn.execute(migration.read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migrations(name) VALUES (%s)", (migration.name,))
        conn.execute(
            "UPDATE review_runs SET status='interrupted',step='Server restarted',completed_at=now() WHERE status IN ('queued','running')"
        )
    with psycopg.connect(DATABASE_URL, client_encoding="utf8") as conn:
        flags = conn.execute(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        if flags[0] or flags[1]:
            raise RuntimeError("Runtime database role must not bypass row security")


@contextmanager
def transaction(actor=None, org_id=None):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, client_encoding="utf8") as conn:
        if actor:
            conn.execute("SELECT set_config('app.user_id', %s, true)", (str(actor["id"]),))
            conn.execute("SELECT set_config('app.email', %s, true)", (actor["email"],))
        if org_id:
            conn.execute("SELECT set_config('app.org_id', %s, true)", (str(org_id),))
        yield conn


def set_org(conn, org_id):
    conn.execute("SELECT set_config('app.org_id', %s, true)", (str(org_id),))


def audit(conn, actor_id, org_id, action, target_type, target_id, metadata=None):
    from psycopg.types.json import Jsonb

    conn.execute(
        "INSERT INTO audit_events(org_id,actor_id,action,target_type,target_id,metadata) VALUES (%s,%s,%s,%s,%s,%s)",
        (org_id, actor_id, action, target_type, str(target_id), Jsonb(metadata or {})),
    )
