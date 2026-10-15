from apps.connectors.providers.ctftime.client import CTFtimeClient
from apps.connectors.providers.ctftime.domain import (
    CTFProfileData,
    CTFSyncData,
    CTFYearlyRankingData,
)
from apps.connectors.providers.ctftime.exceptions import CTFtimeInvalidResponseError
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

    def get_sync_data(self, team_id: str) -> CTFSyncData:
        payload = self.client.get_team_info(team_id)
        profile = self.mapper.map_profile(payload)
        if profile.team_id != team_id:
            raise CTFtimeInvalidResponseError("CTFtime returned a different team ID")
        return CTFSyncData(
            profile=profile,
            yearly_rankings=self.mapper.map_rankings(payload),
        )
