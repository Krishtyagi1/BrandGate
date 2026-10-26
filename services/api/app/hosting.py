"""Hosted startup validation and restricted database login provisioning."""

from urllib.parse import urlsplit

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo


def prepare_environment(environ):
    env = dict(environ)
    admin_url = env.get("DATABASE_ADMIN_URL", "")
    password = env.get("DATABASE_APP_PASSWORD", "")
    origin = env.get("WEB_ORIGIN") or env.get("RENDER_EXTERNAL_URL") or (
        "https://" + env["RAILWAY_PUBLIC_DOMAIN"] if env.get("RAILWAY_PUBLIC_DOMAIN") else ""
    )
    parsed = urlsplit(origin)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Set WEB_ORIGIN to the exact HTTPS public origin.")
    try:
        port = int(env.get("PORT", "8080"))
    except ValueError:
        raise ValueError("PORT must be a valid public port.") from None
    if not 1024 <= port <= 65535 or port == 8000:
        raise ValueError("PORT must be unprivileged and distinct from the internal API port.")
    if not admin_url or not password:
        raise ValueError("Separate migration credentials and an application password are required.")
    try:
        options = conninfo_to_dict(admin_url)
    except psycopg.ProgrammingError:
        raise ValueError("Migration connection configuration is invalid.") from None
    env.update(
        DATABASE_URL=make_conninfo(**{**options, "user": "inkloom_app", "password": password}),
        WEB_ORIGIN=origin,
        COOKIE_SECURE="true",
        PORT=str(port),
    )
    return env


def bootstrap_database(admin_url, password, *, role_name="inkloom_app"):
    """Create a login only when absent; never weaken or reset an existing role."""
    with psycopg.connect(admin_url) as conn:
        flags = conn.execute(
            "SELECT rolsuper,rolbypassrls,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=%s",
            (role_name,),
        ).fetchone()
        if flags and any(flags):
            raise ValueError("Existing runtime database role is privileged.")
        if flags is None:
            conn.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS"
                ).format(sql.Identifier(role_name), sql.Literal(password))
            )
        database = conn.execute("SELECT current_database()").fetchone()[0]
        conn.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(database), sql.Identifier(role_name)
            )
        )
