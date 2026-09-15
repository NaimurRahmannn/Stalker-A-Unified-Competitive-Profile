from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CTFProfileData:
    team_id: str
    name: str
    country: str | None
    logo_url: str | None


@dataclass(frozen=True, slots=True)
class CTFYearlyRankingData:
    year: int
    global_rank: int | None
    country_rank: int | None
    rating_points: float
    organizer_points: float


@dataclass(frozen=True, slots=True)
class CTFSyncData:
    """Complete provider-independent payload required for one atomic sync."""

    profile: CTFProfileData
    yearly_rankings: tuple[CTFYearlyRankingData, ...]
