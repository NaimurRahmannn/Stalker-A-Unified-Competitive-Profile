from datetime import datetime
from typing import Any

from django.utils import timezone


def _timestamp_to_datetime(timestamp: int | None) -> datetime | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())


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
        problem = submission.get("problem") or {}
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
    }
