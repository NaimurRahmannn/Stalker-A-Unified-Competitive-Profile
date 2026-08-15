from datetime import datetime
from typing import Any

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.connectors.base.exceptions import ProviderSchemaError
from apps.connectors.models import PlatformRatingEvent


ATCODER_CONTEST_HOST_SUFFIX = ".contest.atcoder.jp"


def _schema_error(index: int, field: str) -> ProviderSchemaError:
    return ProviderSchemaError(
        f"AtCoder rating history entry {index} has an invalid {field} field."
    )


def _required_text(value: Any, index: int, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _schema_error(index, field)
    return value.strip()


def _optional_text(value: Any, index: int, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise _schema_error(index, field)
    value = value.strip()
    return value or None


def _required_bool(value: Any, index: int, field: str) -> bool:
    if not isinstance(value, bool):
        raise _schema_error(index, field)
    return value


def _optional_int(value: Any, index: int, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise _schema_error(index, field)
    return value


def _required_int(value: Any, index: int, field: str) -> int:
    parsed = _optional_int(value, index, field)
    if parsed is None:
        raise _schema_error(index, field)
    return parsed


def _parse_occurred_at(value: Any, index: int) -> datetime:
    raw = _required_text(value, index, "EndTime")
    parsed = parse_datetime(raw)
    if parsed is None or timezone.is_naive(parsed):
        raise _schema_error(index, "EndTime")
    return parsed


def _contest_id(screen_name: str) -> str:
    if screen_name.endswith(ATCODER_CONTEST_HOST_SUFFIX):
        return screen_name[: -len(ATCODER_CONTEST_HOST_SUFFIX)]
    return screen_name


def normalize_algorithm_rating_history(
    raw_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for index, entry in enumerate(raw_history):
        if not isinstance(entry, dict):
            raise ProviderSchemaError(
                f"AtCoder rating history entry {index} is not an object."
            )

        is_rated = _required_bool(entry.get("IsRated"), index, "IsRated")
        screen_name = _required_text(
            entry.get("ContestScreenName"),
            index,
            "ContestScreenName",
        )
        old_rating = (
            _required_int(entry.get("OldRating"), index, "OldRating")
            if is_rated
            else _optional_int(entry.get("OldRating"), index, "OldRating")
        )
        new_rating = (
            _required_int(entry.get("NewRating"), index, "NewRating")
            if is_rated
            else _optional_int(entry.get("NewRating"), index, "NewRating")
        )

        normalized.append(
            {
                "discipline": PlatformRatingEvent.Discipline.ALGORITHM,
                "external_contest_id": _contest_id(screen_name),
                "contest_name": _optional_text(
                    entry.get("ContestName"), index, "ContestName"
                ),
                "rank": _optional_int(entry.get("Place"), index, "Place"),
                "performance": _optional_int(
                    entry.get("Performance"), index, "Performance"
                ),
                "inner_performance": _optional_int(
                    entry.get("InnerPerformance"), index, "InnerPerformance"
                ),
                "old_rating": old_rating,
                "new_rating": new_rating,
                "rating_change": (
                    new_rating - old_rating
                    if new_rating is not None and old_rating is not None
                    else None
                ),
                "is_rated": is_rated,
                "occurred_at": _parse_occurred_at(entry.get("EndTime"), index),
                "metadata": {
                    "contest_screen_name": screen_name,
                    **(
                        {"contest_name_en": entry["ContestNameEn"].strip()}
                        if isinstance(entry.get("ContestNameEn"), str)
                        and entry["ContestNameEn"].strip()
                        else {}
                    ),
                },
            }
        )

    normalized.sort(
        key=lambda event: (event["occurred_at"], event["external_contest_id"])
    )
    return normalized


def derive_algorithm_stats(events: list[dict[str, Any]]) -> dict[str, Any]:
    rated = [event for event in events if event["is_rated"]]
    if not rated:
        return {
            "current_rating": None,
            "max_rating": None,
            "rated_contest_count": 0,
            "last_rated_at": None,
            "last_performance": None,
        }

    latest = rated[-1]
    ratings = [event["new_rating"] for event in rated]
    return {
        "current_rating": latest["new_rating"],
        "max_rating": max(ratings),
        "rated_contest_count": len(rated),
        "last_rated_at": latest["occurred_at"],
        "last_performance": latest["performance"],
    }


def get_atcoder_rating_color(rating: int | None) -> str | None:
    if rating is None:
        return None
    if rating < 400:
        return "gray"
    if rating < 800:
        return "brown"
    if rating < 1200:
        return "green"
    if rating < 1600:
        return "cyan"
    if rating < 2000:
        return "blue"
    if rating < 2400:
        return "yellow"
    if rating < 2800:
        return "orange"
    return "red"
