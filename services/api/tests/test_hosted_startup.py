import os
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from app.hosting import bootstrap_database, prepare_environment


def hosted_env(**changes):
    return {
        "DATABASE_ADMIN_URL": os.environ["DATABASE_ADMIN_URL"],
        "DATABASE_APP_PASSWORD": "synthetic /@:' password",
        "RAILWAY_PUBLIC_DOMAIN": "brandgate-test.up.railway.app",
        "PORT": "8080",
        **changes,
    }


def test_hosted_credentials_preserve_connection_options_and_escape_password():
    env = prepare_environment(hosted_env())
    runtime = conninfo_to_dict(env["DATABASE_URL"])
    assert runtime["user"] == "inkloom_app"
    assert runtime["password"] == "synthetic /@:' password"
    assert runtime["dbname"] == "inkloom_test_utf8"
    assert env["WEB_ORIGIN"] == "https://brandgate-test.up.railway.app"
    assert env["COOKIE_SECURE"] == "true"


def test_render_public_origin_is_used_without_a_manual_override():
    env = prepare_environment(
        hosted_env(RAILWAY_PUBLIC_DOMAIN="", RENDER_EXTERNAL_URL="https://brandgate-demo.onrender.com")
    )
    assert env["WEB_ORIGIN"] == "https://brandgate-demo.onrender.com"


@pytest.mark.parametrize(
    "changes",
    [
        {"DATABASE_ADMIN_URL": ""},
        {"DATABASE_APP_PASSWORD": ""},
        {"WEB_ORIGIN": "http://public.example.com"},
        {"WEB_ORIGIN": "https://public.example.com/path"},
        {"WEB_ORIGIN": "https://user:password@public.example.com"},
        {"RAILWAY_PUBLIC_DOMAIN": ""},
        {"PORT": "8000"},
        {"PORT": "not-a-port"},
    ],
)
def test_hosted_startup_rejects_missing_or_unsafe_config(changes):
    with pytest.raises(ValueError):
        prepare_environment(hosted_env(**changes))


def test_bootstrap_creates_restricted_login_and_rejects_privileged_existing_role():
    role = "hosted_test_" + uuid4().hex
    admin_url = os.environ["DATABASE_ADMIN_URL"]
    try:
        bootstrap_database(admin_url, "synthetic password", role_name=role)
        with psycopg.connect(admin_url, autocommit=True) as conn:
            flags = conn.execute(
                "SELECT rolsuper,rolbypassrls,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=%s",
                (role,),
            ).fetchone()
            assert flags == (False, False, False, False)
            conn.execute(sql.SQL("ALTER ROLE {} CREATEDB").format(sql.Identifier(role)))
        with pytest.raises(ValueError, match="privileged"):
            bootstrap_database(admin_url, "synthetic password", role_name=role)
    finally:
        with psycopg.connect(admin_url, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            conn.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
