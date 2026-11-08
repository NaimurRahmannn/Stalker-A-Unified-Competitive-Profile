from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ParsedKaggleProfile:
    username: str
    observed_at: datetime
    tracks: dict[str, dict[str, Any]]
    source: str = "offline_fixture_v1"


@dataclass(frozen=True)
class NormalizedKaggleTrack:
    track: str
    rank_status: str
    values: dict[str, int | str | Decimal | None]
    provided_fields: frozenset[str]


@dataclass(frozen=True)
class NormalizedKaggleProfile:
    username: str
    observed_at: datetime
    source: str
    tracks: tuple[NormalizedKaggleTrack, ...]
