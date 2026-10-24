"""Immutable copies of approved knowledge; version rows are the visible collection."""

import json
from uuid import uuid4

from psycopg.types.json import Jsonb

DEFAULT_CHECKS = [
    "prices",
    "claims",
    "tone",
    "language",
    "required_wording",
    "colours_fonts",
    "logos",
    "accessibility",
]


def current_snapshot(conn, org_id, version_id):
    return conn.execute(
        "SELECT * FROM knowledge_snapshots WHERE org_id=%s AND guideline_version_id=%s ORDER BY sequence DESC LIMIT 1",
        (org_id, version_id),
    ).fetchone()


def snapshot_rules(conn, org_id, snapshot_id, channel=None):
    snapshot = conn.execute(
        "SELECT rules FROM knowledge_snapshots WHERE org_id=%s AND id=%s", (org_id, snapshot_id)
    ).fetchone()
    if not snapshot:
        return []
    return [
        r
        for r in snapshot["rules"]
        if channel is None or r.get("scope_channel", "global") in ("global", channel)
    ]


def append_snapshot(conn, org_id, version, rules, actor_id):
    """Caller holds the organisation/version lock. Copies never change later."""
    previous = current_snapshot(conn, org_id, version["id"])
    references = []
    for rule in rules:
        if rule_check(rule) != "logos" or not rule.get("source_document_id"):
            continue
        source = conn.execute(
            "SELECT * FROM source_documents WHERE org_id=%s AND id=%s",
            (org_id, rule["source_document_id"]),
        ).fetchone()
        if source and source["media_type"] in ("image/png", "image/jpeg"):
            references.append(
                {
                    "id": str(rule["id"]),
                    "label": rule["value"],
                    "private_path": source["private_path"],
                    "sha256": source["sha256"],
                    "source_document_id": str(source["id"]),
                    "source_location": rule["source_location"],
                    "source_excerpt": rule["source_excerpt"],
                    "value": rule["value"],
                    "media_type": source["media_type"],
                }
            )
    row = conn.execute(
        'INSERT INTO knowledge_snapshots(id,org_id,guideline_version_id,sequence,checks,instructions,rules,"references",approved_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',
        (
            uuid4(),
            org_id,
            version["id"],
            previous["sequence"] + 1 if previous else 1,
            Jsonb(version["checks"]),
            version["instructions"],
            Jsonb(json.loads(json.dumps(rules, default=str))),
            Jsonb(references),
            actor_id,
        ),
    ).fetchone()
    conn.execute(
        "UPDATE approval_requests SET status='superseded' WHERE org_id=%s AND status='pending'",
        (org_id,),
    )
    conn.execute(
        "UPDATE drafts SET status='draft' WHERE org_id=%s AND status='pending_approval'", (org_id,)
    )
    return row


def snapshot_references(conn, org_id, snapshot_id):
    row = conn.execute(
        'SELECT "references" FROM knowledge_snapshots WHERE org_id=%s AND id=%s',
        (org_id, snapshot_id),
    ).fetchone()
    return row["references"] if row else []


def rule_identity(rule):
    fact = rule.get("fact")
    if fact and fact.get("kind") == "price":
        return (
            "price",
            *(
                str(fact.get(k, "")).casefold()
                for k in ("entity", "currency", "unit", "effective_from", "effective_to")
            ),
            rule.get("scope_channel", "global"),
        )
    return (rule["type"], rule["rule_key"].casefold(), rule.get("scope_channel", "global"))


def rules_overlap(left, right):
    a, b = left.get("fact"), right.get("fact")
    if a and b and a.get("kind") == b.get("kind") == "price":
        if any(
            str(a.get(key, "")).strip().casefold() != str(b.get(key, "")).strip().casefold()
            for key in ("entity", "currency", "unit")
        ):
            return False
        scopes = {left.get("scope_channel", "global"), right.get("scope_channel", "global")}
        if len(scopes) > 1 and "global" not in scopes:
            return False
        return max(str(a["effective_from"]), str(b["effective_from"])) <= min(
            str(a.get("effective_to") or "9999-12-31"), str(b.get("effective_to") or "9999-12-31")
        )
    return rule_identity(left) == rule_identity(right)


def rule_check(rule):
    if rule.get("check"):
        return rule["check"]
    if rule.get("fact"):
        return "prices"
    if rule["type"] == "approved_fact" and "price" in rule["rule_key"]:
        return "prices"
    return {
        "tone": "tone",
        "product_name": "language",
        "prohibited_term": "language",
        "required_disclaimer": "required_wording",
        "channel_instruction": "tone",
    }.get(rule["type"], "claims")
