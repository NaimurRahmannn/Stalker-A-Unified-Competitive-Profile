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
            team_id = str(payload["id"])
            name = str(payload["name"])
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
            global_rank = year_stats.get("rating_place")
            global_rank = int(global_rank) if global_rank is not None else None

            country_rank = year_stats.get("country_place")
            country_rank = int(country_rank) if country_rank is not None else None

            # Sometimes points are 0 or missing, but we expect them to be floats
            try:
                rating_points = float(year_stats.get("rating_points", 0.0))
                organizer_points = float(year_stats.get("organizer_points", 0.0))
            except (ValueError, TypeError):
                rating_points = 0.0
                organizer_points = 0.0

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
