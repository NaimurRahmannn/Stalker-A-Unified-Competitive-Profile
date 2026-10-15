import math
import re
from typing import Any

from apps.connectors.providers.ctftime.domain import (
    CTFProfileData,
    CTFYearlyRankingData,
)
from apps.connectors.providers.ctftime.exceptions import CTFtimeInvalidResponseError


class CTFtimeMapper:
    """
    Translates raw JSON dictionaries from the CTFtime API into strict STALKER DTOs.
    Validates required fields and applies defensive type casting.
    """

    @staticmethod
    def map_profile(payload: dict[str, Any]) -> CTFProfileData:
        try:
            raw_id = payload["id"]
            raw_name = payload["name"]
            if isinstance(raw_id, bool) or not re.fullmatch(r"[1-9][0-9]*", str(raw_id)):
                raise ValueError("id must be a positive team ID")
            if not isinstance(raw_name, str) or not raw_name.strip():
                raise ValueError("name must be nonempty text")
            team_id = str(raw_id)
            name = raw_name.strip()
        except (KeyError, ValueError, TypeError) as e:
            raise CTFtimeInvalidResponseError(
                f"Missing or invalid required profile fields: {e}"
            ) from e

        country = payload.get("country")
        country = str(country) if country else None

        logo_url = payload.get("logo")
        logo_url = str(logo_url) if logo_url else None

        return CTFProfileData(
            team_id=team_id,
            name=name,
            country=country,
            logo_url=logo_url,
        )

    @staticmethod
    def map_rankings(payload: dict[str, Any]) -> tuple[CTFYearlyRankingData, ...]:
        """
        Extracts yearly rankings from the team payload.
        CTFtime nests these inside a "rating" object grouped by year string.
        """
        rating_data = payload.get("rating", {})
        if not isinstance(rating_data, dict):
            raise CTFtimeInvalidResponseError("Team rating data must be an object")

        rankings = []
        for year_str, year_stats in rating_data.items():
            if not isinstance(year_stats, dict):
                continue

            try:
                year = int(year_str)
            except ValueError:
                continue

            # CTFtime sometimes omits rating_place or country_place if unranked
            try:
                global_rank = (
                    int(year_stats["rating_place"])
                    if year_stats.get("rating_place") is not None
                    else None
                )
                country_rank = (
                    int(year_stats["country_place"])
                    if year_stats.get("country_place") is not None
                    else None
                )
                if any(rank is not None and rank < 0 for rank in (global_rank, country_rank)):
                    raise ValueError("rank cannot be negative")
            except (TypeError, ValueError) as e:
                raise CTFtimeInvalidResponseError(
                    f"Invalid ranking position for {year}"
                ) from e

            # Sometimes points are 0 or missing, but we expect them to be floats
            try:
                rating_points = float(year_stats.get("rating_points") or 0.0)
                organizer_points = float(year_stats.get("organizer_points") or 0.0)
                if not math.isfinite(rating_points) or not math.isfinite(organizer_points):
                    raise ValueError("points must be finite")
            except (ValueError, TypeError) as e:
                raise CTFtimeInvalidResponseError(
                    f"Invalid ranking points for {year}"
                ) from e

            rankings.append(
                CTFYearlyRankingData(
                    year=year,
                    global_rank=global_rank,
                    country_rank=country_rank,
                    rating_points=rating_points,
                    organizer_points=organizer_points,
                )
            )

        # Return sorted by year descending (newest first)
        rankings.sort(key=lambda r: r.year, reverse=True)
        return tuple(rankings)
