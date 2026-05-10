from datetime import datetime
from typing import Any

import requests
from django.utils import timezone


BASE_URL = "https://codeforces.com/api"


class CodeforcesAPIError(Exception):
    pass


class CodeforcesInvalidHandleError(CodeforcesAPIError):
    pass


class CodeforcesUnavailableError(CodeforcesAPIError):
    pass


def _request_codeforces(method: str, params: dict[str, Any], timeout: int) -> Any:
    try:
        response = requests.get(f"{BASE_URL}/{method}", params=params, timeout=timeout)
    except requests.Timeout as exc:
        raise CodeforcesUnavailableError("Codeforces API request timed out.") from exc
    except requests.ConnectionError as exc:
        raise CodeforcesUnavailableError("Codeforces API is currently unavailable.") from exc
    except requests.RequestException as exc:
        raise CodeforcesUnavailableError("Codeforces API request failed.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        if response.status_code >= 500:
            raise CodeforcesUnavailableError("Codeforces API is currently unavailable.") from exc
        raise CodeforcesAPIError("Codeforces API returned an invalid response.") from exc

    status = payload.get("status")
    if status != "OK":
        comment = payload.get("comment") or "Codeforces API returned an error."
        if _is_user_error(comment):
            raise CodeforcesInvalidHandleError(comment)
        raise CodeforcesAPIError(comment)

    if "result" not in payload:
        raise CodeforcesAPIError("Codeforces API response did not include a result.")

    if not response.ok:
        raise CodeforcesUnavailableError(
            f"Codeforces API returned HTTP {response.status_code}."
        )

    return payload["result"]


def _is_user_error(comment: str) -> bool:
    comment_lower = comment.lower()
    user_error_fragments = (
        "not found",
        "handle",
        "user",
        "should contain",
        "invalid",
    )
    return any(fragment in comment_lower for fragment in user_error_fragments)


def _timestamp_to_datetime(timestamp: int | None) -> datetime | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.get_current_timezone())


def fetch_user_info(handle: str) -> dict:
    result = _request_codeforces(
        "user.info",
        {"handles": handle},
        timeout=10,
    )
    if not isinstance(result, list) or not result:
        raise CodeforcesInvalidHandleError("Codeforces handle was not found.")
    user_info = result[0]
    if not isinstance(user_info, dict):
        raise CodeforcesAPIError("Codeforces user.info returned an unexpected result.")
    return user_info


def fetch_user_submissions(handle: str, count: int = 10000) -> list:
    result = _request_codeforces(
        "user.status",
        {"handle": handle, "from": 1, "count": count},
        timeout=15,
    )
    if not isinstance(result, list):
        raise CodeforcesAPIError("Codeforces user.status returned an unexpected result.")
    return result


def fetch_user_rating(handle: str) -> list:
    result = _request_codeforces(
        "user.rating",
        {"handle": handle},
        timeout=10,
    )
    if not isinstance(result, list):
        raise CodeforcesAPIError("Codeforces user.rating returned an unexpected result.")
    return result


def calculate_solved_stats(submissions: list) -> dict:
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


def _problem_key(problem: dict) -> tuple | None:
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


def build_codeforces_profile(handle: str) -> dict:
    user_info = fetch_user_info(handle)
    canonical_handle = user_info.get("handle") or handle
    submissions = fetch_user_submissions(canonical_handle)
    rating_history = fetch_user_rating(canonical_handle)
    solved_stats = calculate_solved_stats(submissions)

    return {
        "handle": canonical_handle,
        "rating": user_info.get("rating"),
        "max_rating": user_info.get("maxRating"),
        "rank": user_info.get("rank"),
        "max_rank": user_info.get("maxRank"),
        "solved_count": solved_stats["solved_count"],
        "attempted_count": solved_stats["attempted_count"],
        "accepted_submission_count": solved_stats["accepted_submission_count"],
        "contest_count": len(rating_history),
        "last_online_at": _timestamp_to_datetime(user_info.get("lastOnlineTimeSeconds")),
        "registered_at": _timestamp_to_datetime(user_info.get("registrationTimeSeconds")),
        "raw_user_info": user_info,
        "raw_rating_history": rating_history,
    }
