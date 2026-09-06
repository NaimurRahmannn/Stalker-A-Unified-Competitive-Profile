import math
from datetime import timezone as datetime_timezone
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.connectors.models import LeetCodeStats, LeetCodeSyncState, PlatformAccount


def build_leetcode_sync_summary(
    stats: LeetCodeStats | None,
    sync_state: LeetCodeSyncState | None,
) -> dict[str, Any]:
    freshness = stats.data_updated_at if stats else None
    if sync_state is None:
        status = "success" if freshness else "never_synced"
        attempted_at = None
        successful_at = freshness
        error_code = None
    else:
        status = sync_state.status
        attempted_at = sync_state.last_attempted_at
        successful_at = sync_state.last_successful_at
        error_code = sync_state.failure_reason or None

    return {
        "status": status,
        "updated_at": freshness,
        "attempted_at": attempted_at,
        "successful_at": successful_at,
        "using_cached_data": bool(
            freshness
            and sync_state
            and sync_state.status == LeetCodeSyncState.Status.FAILED
        ),
        "error_code": error_code,
    }


def normalize_leetcode_rating_history(stats: LeetCodeStats) -> list[dict[str, Any]]:
    history = stats.rating_history
    if not isinstance(history, list):
        return []

    normalized = []
    for item in history:
        if not isinstance(item, dict):
            continue
        title = item.get("contest_title")
        occurred_at = item.get("occurred_at")
        rating = item.get("rating")
        parsed_at = (
            parse_datetime(occurred_at)
            if isinstance(occurred_at, str)
            else None
        )
        if (
            not isinstance(title, str)
            or not title.strip()
            or parsed_at is None
            or isinstance(rating, bool)
            or not isinstance(rating, (int, float))
            or not math.isfinite(rating)
        ):
            continue
        if timezone.is_naive(parsed_at):
            parsed_at = timezone.make_aware(parsed_at, datetime_timezone.utc)
        normalized.append(
            {
                "platform": PlatformAccount.Platform.LEETCODE,
                "contest_title": title.strip(),
                "occurred_at": parsed_at,
                "new_rating": float(rating),
                "ranking": _optional_non_negative_int(item.get("ranking")),
                "problems_solved": _optional_non_negative_int(
                    item.get("problems_solved")
                ),
                "total_problems": _optional_non_negative_int(
                    item.get("total_problems")
                ),
                "finish_time_seconds": _optional_non_negative_int(
                    item.get("finish_time_seconds")
                ),
            }
        )

    normalized.sort(
        key=lambda event: (
            event["occurred_at"],
            event["contest_title"],
        )
    )
    previous_rating = None
    for event in normalized:
        event["old_rating"] = previous_rating
        event["rating_change"] = (
            event["new_rating"] - previous_rating
            if previous_rating is not None
            else None
        )
        previous_rating = event["new_rating"]
    return normalized


def _optional_non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
