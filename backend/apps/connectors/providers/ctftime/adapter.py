from apps.connectors.providers.ctftime.client import CTFtimeClient
from apps.connectors.providers.ctftime.domain import (
    CTFProfileData,
    CTFYearlyRankingData,
)
from apps.connectors.providers.ctftime.mapper import CTFtimeMapper


class CTFtimeAdapter:
    """
    Implements the STALKER CTFProvider protocol for CTFtime.
    Composes the CTFtimeClient and CTFtimeMapper to isolate provider mechanics.
    """

    def __init__(self, client: CTFtimeClient) -> None:
        self.client = client
        self.mapper = CTFtimeMapper()

    def get_profile(self, team_id: str) -> CTFProfileData:
        payload = self.client.get_team_info(team_id)
        return self.mapper.map_profile(payload)

    def get_yearly_rankings(self, team_id: str) -> tuple[CTFYearlyRankingData, ...]:
        payload = self.client.get_team_info(team_id)
        return self.mapper.map_rankings(payload)
