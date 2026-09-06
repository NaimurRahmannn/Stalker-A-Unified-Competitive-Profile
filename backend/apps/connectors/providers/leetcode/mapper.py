import math
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from apps.connectors.providers.leetcode.domain import (
    LeetCodeContestStatsData,
    LeetCodeProblemStatsData,
    LeetCodeProfileData,
    LeetCodeRatingEventData,
)
from apps.connectors.providers.leetcode.exceptions import LeetCodeInvalidResponseError


def _error(context: str, field: str) -> LeetCodeInvalidResponseError:
    return LeetCodeInvalidResponseError(
        f"LeetCode {context} response has an invalid {field} field."
    )


def _required_text(value: Any, context: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(context, field)
    return value.strip()


def _optional_text(value: Any, context: str, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise _error(context, field)
    normalized = value.strip()
    return normalized or None


def _required_non_negative_int(value: Any, context: str, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _error(context, field)
    return value


def _optional_non_negative_int(
    value: Any,
    context: str,
    field: str,
) -> int | None:
    if value is None:
        return None
    return _required_non_negative_int(value, context, field)


def _optional_number(value: Any, context: str, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(context, field)
    normalized = float(value)
    if not math.isfinite(normalized):
        raise _error(context, field)
    return normalized


def _required_number(value: Any, context: str, field: str) -> float:
    parsed = _optional_number(value, context, field)
    if parsed is None:
        raise _error(context, field)
    return parsed


def map_alfa_profile(payload: dict[str, Any]) -> LeetCodeProfileData:
    context = "profile"
    handle = _required_text(payload.get("username"), context, "username")
    return LeetCodeProfileData(
        handle=handle,
        profile_url=f"https://leetcode.com/u/{quote(handle, safe='')}/",
        display_name=_optional_text(payload.get("name"), context, "name"),
        avatar_url=_optional_text(payload.get("avatar"), context, "avatar"),
        country=_optional_text(payload.get("country"), context, "country"),
        organization=_optional_text(payload.get("company"), context, "company"),
        school=_optional_text(payload.get("school"), context, "school"),
        global_problem_ranking=_optional_non_negative_int(
            payload.get("ranking"), context, "ranking"
        ),
        reputation=_optional_non_negative_int(
            payload.get("reputation"), context, "reputation"
        ),
    )


def map_alfa_problem_stats(payload: dict[str, Any]) -> LeetCodeProblemStatsData:
    context = "problem statistics"
    return LeetCodeProblemStatsData(
        solved_total=_required_non_negative_int(
            payload.get("solvedProblem"), context, "solvedProblem"
        ),
        solved_easy=_required_non_negative_int(
            payload.get("easySolved"), context, "easySolved"
        ),
        solved_medium=_required_non_negative_int(
            payload.get("mediumSolved"), context, "mediumSolved"
        ),
        solved_hard=_required_non_negative_int(
            payload.get("hardSolved"), context, "hardSolved"
        ),
        stats_complete=True,
    )


def map_alfa_contest_stats(payload: dict[str, Any]) -> LeetCodeContestStatsData:
    context = "contest statistics"
    top_percentage = _optional_number(
        payload.get("contestTopPercentage"), context, "contestTopPercentage"
    )
    if top_percentage is not None and not 0 <= top_percentage <= 100:
        raise _error(context, "contestTopPercentage")

    return LeetCodeContestStatsData(
        current_rating=_optional_number(
            payload.get("contestRating"), context, "contestRating"
        ),
        attended_contest_count=_required_non_negative_int(
            payload.get("contestAttend"), context, "contestAttend"
        ),
        global_ranking=_optional_non_negative_int(
            payload.get("contestGlobalRanking"), context, "contestGlobalRanking"
        ),
        total_participants=_optional_non_negative_int(
            payload.get("totalParticipants"), context, "totalParticipants"
        ),
        top_percentage=top_percentage,
    )


def map_alfa_rating_history(
    payload: dict[str, Any],
) -> tuple[LeetCodeRatingEventData, ...]:
    raw_history = payload.get("contestHistory")
    if not isinstance(raw_history, list):
        raise _error("rating history", "contestHistory")

    events = []
    for index, entry in enumerate(raw_history):
        context = f"rating history entry {index}"
        if not isinstance(entry, dict):
            raise _error(context, "entry")
        attended = entry.get("attended")
        if not isinstance(attended, bool):
            raise _error(context, "attended")
        if not attended:
            continue

        contest = entry.get("contest")
        if not isinstance(contest, dict):
            raise _error(context, "contest")
        start_time = _required_non_negative_int(
            contest.get("startTime"), context, "contest.startTime"
        )

        events.append(
            LeetCodeRatingEventData(
                contest_title=_required_text(
                    contest.get("title"), context, "contest.title"
                ),
                occurred_at=datetime.fromtimestamp(start_time, tz=timezone.utc),
                rating=_required_number(entry.get("rating"), context, "rating"),
                ranking=_optional_non_negative_int(
                    entry.get("ranking"), context, "ranking"
                ),
                problems_solved=_optional_non_negative_int(
                    entry.get("problemsSolved"), context, "problemsSolved"
                ),
                total_problems=_optional_non_negative_int(
                    entry.get("totalProblems"), context, "totalProblems"
                ),
                finish_time_seconds=_optional_non_negative_int(
                    entry.get("finishTimeInSeconds"),
                    context,
                    "finishTimeInSeconds",
                ),
                attended=True,
            )
        )

    events.sort(key=lambda event: (event.occurred_at, event.contest_title))
    return tuple(events)
