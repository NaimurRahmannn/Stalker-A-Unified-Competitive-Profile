from datetime import datetime
from typing import Any

from django.utils import timezone


RECENT_ACTIVITY_LIMIT = 20


def _timestamp_to_datetime(timestamp: int | None) -> datetime | None:
    if not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool):
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())


def _timestamp_to_iso(timestamp: int | None) -> str | None:
    value = _timestamp_to_datetime(timestamp)
    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _problem_key(problem: dict[str, Any]) -> tuple | None:
    index = problem.get("index")
    contest_id = problem.get("contestId")
    if contest_id is not None and index:
        return ("contest", contest_id, index)

    name = problem.get("name")
    if name and index:
        return ("fallback", name, index)

    if name:
        return ("fallback", name)

    return None


def calculate_solved_stats(submissions: list[dict[str, Any]]) -> dict[str, int]:
    solved_problems = set()
    attempted_problems = set()
    accepted_submission_count = 0

    for submission in submissions:
        if not isinstance(submission, dict):
            continue
        problem = submission.get("problem") or {}
        if not isinstance(problem, dict):
            continue
        problem_key = _problem_key(problem)
        if problem_key is None:
            continue

        attempted_problems.add(problem_key)

        if submission.get("verdict") == "OK":
            solved_problems.add(problem_key)
            accepted_submission_count += 1

    return {
        "solved_count": len(solved_problems),
        "attempted_count": len(attempted_problems),
        "accepted_submission_count": accepted_submission_count,
    }


def normalize_rating_history(
    rating_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized = []

    for entry in rating_history:
        if not isinstance(entry, dict):
            continue

        timestamp = _timestamp_to_iso(entry.get("ratingUpdateTimeSeconds"))
        new_rating = _optional_int(entry.get("newRating"))
        if timestamp is None or new_rating is None:
            continue

        old_rating = _optional_int(entry.get("oldRating"))
        normalized.append(
            {
                "contest_id": _optional_int(entry.get("contestId")),
                "contest_name": _optional_text(entry.get("contestName")),
                "rank": _optional_int(entry.get("rank")),
                "old_rating": old_rating,
                "new_rating": new_rating,
                "rating_change": (
                    new_rating - old_rating if old_rating is not None else None
                ),
                "timestamp": timestamp,
            }
        )

    return sorted(normalized, key=lambda item: item["timestamp"])


def normalize_recent_activity(
    submissions: list[dict[str, Any]],
    limit: int = RECENT_ACTIVITY_LIMIT,
) -> list[dict[str, Any]]:
    normalized = []

    for submission in submissions:
        if not isinstance(submission, dict):
            continue
        problem = submission.get("problem") or {}
        if not isinstance(problem, dict):
            continue

        problem_name = _optional_text(problem.get("name"))
        submitted_at = _timestamp_to_iso(submission.get("creationTimeSeconds"))
        if problem_name is None or submitted_at is None:
            continue

        normalized.append(
            {
                "submission_id": _optional_int(submission.get("id")),
                "contest_id": _optional_int(
                    submission.get("contestId") or problem.get("contestId")
                ),
                "problem_index": _optional_text(problem.get("index")),
                "problem_name": problem_name,
                "problem_rating": _optional_int(problem.get("rating")),
                "verdict": _optional_text(submission.get("verdict")) or "UNKNOWN",
                "language": _optional_text(submission.get("programmingLanguage")),
                "submitted_at": submitted_at,
            }
        )

    normalized.sort(key=lambda item: item["submitted_at"], reverse=True)
    return normalized[: max(0, limit)]


def map_codeforces_profile(
    raw_user: dict[str, Any],
    submissions: list[dict[str, Any]],
    rating_history: list[dict[str, Any]],
    handle: str,
) -> dict[str, Any]:
    canonical_handle = raw_user.get("handle") or handle
    solved_stats = calculate_solved_stats(submissions)

    return {
        "handle": canonical_handle,
        "rating": raw_user.get("rating"),
        "max_rating": raw_user.get("maxRating"),
        "rank": raw_user.get("rank"),
        "max_rank": raw_user.get("maxRank"),
        "solved_count": solved_stats["solved_count"],
        "attempted_count": solved_stats["attempted_count"],
        "accepted_submission_count": solved_stats["accepted_submission_count"],
        "contest_count": len(rating_history),
        "last_online_at": _timestamp_to_datetime(raw_user.get("lastOnlineTimeSeconds")),
        "registered_at": _timestamp_to_datetime(raw_user.get("registrationTimeSeconds")),
        "raw_user_info": raw_user,
        "raw_rating_history": rating_history,
        "recent_activity": normalize_recent_activity(submissions),
    }
