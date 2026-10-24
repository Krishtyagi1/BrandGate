import re


def load_policy(conn, org_id, version_id, channel):
    return conn.execute(
        "SELECT id,type,rule_key,value,scope_channel,source_document_id,source_excerpt,source_location,fact FROM structured_rules WHERE org_id=%s AND guideline_version_id=%s AND approved_by IS NOT NULL AND scope_channel IN ('global',%s) ORDER BY created_at,id",
        (org_id, version_id, channel),
    ).fetchall()


def retrieve(rules, text, limit=24):
    words = set(re.findall(r"\w+", text.casefold()))

    def score(rule):
        return len(words & set(re.findall(r"\w+", rule["value"].casefold()))) + (
            10 if rule["type"] in ("prohibited_term", "required_disclaimer", "tone") else 0
        )

    return sorted(rules, key=lambda r: (-score(r), str(r["id"])))[:limit]


def evidence(rule):
    return {
        "id": str(rule["id"]),
        "type": rule["type"],
        "rule_key": rule["rule_key"],
        "value": rule["value"],
        "excerpt": rule.get("source_excerpt") or rule["value"],
        "location": rule.get("source_location") or "Owner-approved structured rule",
        "source_document_id": str(rule["source_document_id"])
        if rule.get("source_document_id")
        else None,
    }
