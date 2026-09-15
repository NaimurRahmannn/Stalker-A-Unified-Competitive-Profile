from typing import Protocol, runtime_checkable

from apps.connectors.providers.ctftime.domain import (
    CTFProfileData,
    CTFYearlyRankingData,
)


@runtime_checkable
class CTFProvider(Protocol):
    """Stable STALKER contract for any future CTF data source."""

    def get_profile(self, team_id: str) -> CTFProfileData: ...

    def get_yearly_rankings(self, team_id: str) -> tuple[CTFYearlyRankingData, ...]: ...
