"""Canonical references used by both account linking and imports."""

import hashlib
import re
from urllib.parse import urlsplit

from rest_framework.exceptions import ValidationError


USERNAME = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
HOST = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*\Z")
SLUG = re.compile(r"[A-Za-z0-9_-]{1,150}\Z")


def _parts(value: str, *, allow_query=False, allow_port=False):
    if not isinstance(value, str):
        raise ValidationError("Enter a valid URL of at most 500 characters.")
    value = value.strip()
    if not value or len(value) > 500:
        raise ValidationError("Enter a valid URL of at most 500 characters.")
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise ValidationError("Enter a valid URL.") from exc
    host = (parts.hostname or "").lower()
    if (parts.scheme.lower() not in {"http", "https"} or not host or len(host) > 253 or
            not HOST.fullmatch(host) or ".." in host or
            parts.username is not None or parts.password is not None or
            (port is not None and not allow_port) or (not allow_query and ("?" in value or "#" in value)) or
            parts.path.startswith("//") or
            "\\" in value or any(ord(c) < 32 for c in value)):
        raise ValidationError("Enter an HTTP(S) URL without credentials, port, query, or fragment.")
    return parts, host


def profile_reference(value: str) -> tuple[str, str]:
    value = value.strip() if isinstance(value, str) else ""
    if "://" in value:
        parts, host = _parts(value)
        if host not in {"devpost.com", "www.devpost.com"}:
            raise ValidationError("Enter a devpost.com profile URL.")
        match = re.fullmatch(r"/([A-Za-z0-9_-]{1,64})/?", parts.path)
        if not match:
            raise ValidationError("Enter a Devpost profile path only.")
        value = match.group(1)
    if not USERNAME.fullmatch(value) or value.lower() in {"software", "hackathons", "users"}:
        raise ValidationError("Enter a valid Devpost username.")
    handle = value.lower()
    return handle, f"https://devpost.com/{handle}"


def project_reference(value: str) -> str:
    parts, host = _parts(value)
    match = re.fullmatch(r"/software/([A-Za-z0-9_-]{1,150})/?", parts.path, re.IGNORECASE)
    if host not in {"devpost.com", "www.devpost.com"} or not match:
        raise ValidationError("Enter a Devpost software project URL.")
    return f"https://devpost.com/software/{match.group(1).lower()}"


def event_reference(value: str) -> str:
    parts, host = _parts(value)
    if not host.endswith(".devpost.com") or host in {"www.devpost.com", "devpost.com"}:
        raise ValidationError("Enter a Devpost hackathon subdomain URL.")
    subdomain = host.removesuffix(".devpost.com")
    if not SLUG.fullmatch(subdomain) or parts.path not in {"", "/"}:
        raise ValidationError("Enter a Devpost hackathon subdomain URL.")
    return f"https://{host}/"


def external_url(value: str) -> str:
    parts, _ = _parts(value, allow_query=True, allow_port=True)
    if not parts.path and not parts.netloc:
        raise ValidationError("Enter a valid HTTP(S) URL.")
    return value.strip()


def external_id(kind: str, handle: str, *references: str) -> str:
    digest = hashlib.sha256("\x00".join((handle, *references)).encode()).hexdigest()
    return f"{kind}:{digest}"
