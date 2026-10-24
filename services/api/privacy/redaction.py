import re

PATTERN = re.compile(
    r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|(?<!\w)(?:\+?\d[\d ()-]{8,}\d)(?!\w)|\b(?:sk-or-v1-|sk-)[A-Za-z0-9_-]{12,}|\b(?:password|api[_ -]?key|secret)\s*[:=]\s*\S+"
)
TOKEN = re.compile(r"\[PRIVATE_\d+\]")


def redact(text):
    values, reverse = {}, {}

    def replace(match):
        value = match.group(0)
        if value not in reverse:
            token = f"[PRIVATE_{len(values) + 1}]"
            values[token] = value
            reverse[value] = token
        return reverse[value]

    # User-authored reserved tokens could otherwise collide with redaction mappings.
    if TOKEN.search(text):
        raise ValueError("Remove reserved [PRIVATE_n] tokens from the document before review.")
    return PATTERN.sub(replace, text), values


def restore(text, values):
    if any(token not in values for token in TOKEN.findall(text)):
        raise ValueError("An unknown protected token was returned.")
    for token, value in values.items():
        text = text.replace(token, value)
    return text
