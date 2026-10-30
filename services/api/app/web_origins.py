"""Exact extra public origins, without wildcards or permissive suffix matching."""

from urllib.parse import urlsplit


def allowed_web_origins(primary, additional=""):
    origins = {primary}
    for value in additional.split(","):
        origin = value.strip()
        if not origin:
            continue
        try:
            parsed = urlsplit(origin)
            port = parsed.port
            valid = (
                parsed.scheme == "https"
                and parsed.hostname
                and "*" not in origin
                and not parsed.username
                and not parsed.password
                and not parsed.path
                and not parsed.query
                and not parsed.fragment
                and (port is None or 1 <= port <= 65535)
            )
        except ValueError:
            valid = False
        if not valid:
            raise ValueError(
                "Additional web origins must be exact HTTPS origins without paths, credentials or wildcards."
            )
        origins.add(origin)
    return frozenset(origins)
