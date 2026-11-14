"""Small, owner-independent contest feed from CLIST's authenticated API."""

from datetime import datetime, timezone as datetime_timezone
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime


CLIST_CONTEST_URL = "https://clist.by/api/v4/contest/"
CACHE_KEY = "dashboard_clist_upcoming_v1"
SUCCESS_TTL_SECONDS = 600
ERROR_TTL_SECONDS = 60


def _timestamp(value):
    if not isinstance(value, str):
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        return None
    # CLIST's JSON API currently emits UTC datetimes without an offset.
    return parsed if timezone.is_aware(parsed) else parsed.replace(tzinfo=datetime_timezone.utc)


def _safe_event_url(value):
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value)
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        return None
    return value


def normalize_clist_events(payload, *, now: datetime | None = None):
    """Return bounded, safe upcoming and live contests across all CLIST resources."""
    if not isinstance(payload, dict) or not isinstance(payload.get("objects"), list):
        raise ValueError("invalid_clist_payload")
    now = now or timezone.now()
    events = []
    seen = set()
    for item in payload["objects"][:100]:
        if not isinstance(item, dict):
            continue
        event_id = item.get("id")
        title = item.get("event")
        resource = item.get("resource")
        start = _timestamp(item.get("start"))
        end = _timestamp(item.get("end"))
        url = _safe_event_url(item.get("href"))
        if (
            not isinstance(event_id, int) or event_id <= 0 or event_id in seen
            or not isinstance(title, str) or not title.strip()
            or not isinstance(resource, str) or not resource.strip()
            or start is None or end is None or end <= now or end <= start or url is None
        ):
            continue
        seen.add(event_id)
        events.append({
            "id": event_id,
            "title": title.strip()[:180],
            "platform": resource.strip()[:80],
            "start": start.astimezone(datetime_timezone.utc).isoformat(),
            "end": end.astimezone(datetime_timezone.utc).isoformat(),
            "url": url,
            "ongoing": start <= now,
        })
    events.sort(key=lambda event: (
        not event["ongoing"], event["end"] if event["ongoing"] else event["start"], event["id"]
    ))
    return events[:30]


def get_clist_events():
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached
    if not settings.CLIST_API or not settings.CLIST_USERNAME:
        return {"status": "unavailable", "events": [], "reason": "not_configured"}

    try:
        response = requests.get(
            CLIST_CONTEST_URL,
            headers={
                "Authorization": f"ApiKey {settings.CLIST_USERNAME}:{settings.CLIST_API}",
                "Accept": "application/json",
            },
            params={"upcoming": "true", "order_by": "start", "limit": 60, "format": "json"},
            timeout=8,
        )
        if response.status_code != 200:
            raise ValueError("clist_http_error")
        events = normalize_clist_events(response.json())
    except (requests.RequestException, ValueError, TypeError):
        result = {"status": "unavailable", "events": [], "reason": "provider_unavailable"}
        cache.set(CACHE_KEY, result, ERROR_TTL_SECONDS)
        return result

    result = {
        "status": "ready", "events": events,
        "updated_at": timezone.now().isoformat(), "source": "CLIST",
    }
    cache.set(CACHE_KEY, result, SUCCESS_TTL_SECONDS)
    return result
