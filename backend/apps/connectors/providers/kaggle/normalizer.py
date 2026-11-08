import re
from decimal import Decimal, InvalidOperation

from .domain import NormalizedKaggleProfile, NormalizedKaggleTrack, ParsedKaggleProfile
from .exceptions import KaggleDocumentError


TRACKS = frozenset({"competitions", "code", "datasets"})
TIERS = {value.casefold(): value for value in ("Novice", "Contributor", "Expert", "Master", "Grandmaster")}
FIELDS = frozenset({"global_rank", "highest_rank", "tier", "points", "gold_medals", "silver_medals", "bronze_medals"})
RANK_FIELDS = {"global_rank", "highest_rank"}
MEDAL_FIELDS = {"gold_medals", "silver_medals", "bronze_medals"}
MAX_INTEGER = 2**31 - 1


def _integer(value, *, minimum: int, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise KaggleDocumentError("invalid_number", f"{field} is not an integer.")
    text = str(value).strip()
    if not text or not re.fullmatch(r"(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)", text):
        raise KaggleDocumentError("invalid_number", f"{field} is not an integer.")
    if len(text.replace(",", "")) > 10:
        raise KaggleDocumentError("invalid_number", f"{field} is outside the supported range.")
    number = int(text.replace(",", ""))
    if number < minimum or number > MAX_INTEGER:
        raise KaggleDocumentError("invalid_number", f"{field} is outside the supported range.")
    return number


def _points(value) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise KaggleDocumentError("invalid_points", "Points must be a finite decimal number.")
    text = str(value).strip()
    if not re.fullmatch(r"(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]{1,4})?", text):
        raise KaggleDocumentError("invalid_points", "Points must be a finite decimal number.")
    try:
        result = Decimal(text.replace(",", ""))
    except InvalidOperation as exc:
        raise KaggleDocumentError("invalid_points", "Points must be a finite decimal number.") from exc
    if not result.is_finite() or result < 0 or result >= Decimal("10000000000") or result.as_tuple().exponent < -4:
        raise KaggleDocumentError("invalid_points", "Points are outside the supported range or precision.")
    return result


def normalize_profile(parsed: ParsedKaggleProfile) -> NormalizedKaggleProfile:
    normalized = []
    for track, source_values in parsed.tracks.items():
        if track not in TRACKS or not isinstance(source_values, dict):
            raise KaggleDocumentError("invalid_track", "Unknown or malformed Kaggle track.")
        if set(source_values) - (FIELDS | {"rank_status"}):
            raise KaggleDocumentError("unsupported_field", "Unsupported Kaggle ranking field.")
        raw_status = source_values.get("rank_status")
        if raw_status not in (None, "ranked", "unranked", "unknown"):
            raise KaggleDocumentError("invalid_rank_status", "Invalid rank status.")
        values = {}
        for field in FIELDS & source_values.keys():
            value = source_values[field]
            if field in RANK_FIELDS:
                values[field] = _integer(value, minimum=1, field=field)
            elif field in MEDAL_FIELDS:
                values[field] = _integer(value, minimum=0, field=field)
            elif field == "points":
                values[field] = _points(value)
            elif value is None:
                values[field] = None
            elif isinstance(value, str) and value.strip().casefold() in TIERS:
                values[field] = TIERS[value.strip().casefold()]
            else:
                raise KaggleDocumentError("invalid_tier", "Unknown Kaggle tier.")
        if raw_status == "unranked" and any(values.get(field) is not None for field in ("global_rank", "tier", "points")):
            raise KaggleDocumentError("invalid_rank_status", "Unranked track cannot have a current rank, tier or points.")
        if raw_status == "ranked" and values.get("global_rank") is None and values.get("tier") is None:
            raise KaggleDocumentError("invalid_rank_status", "Ranked track requires a rank or tier.")
        if raw_status == "unknown" and (values.get("global_rank") is not None or values.get("tier") is not None):
            raise KaggleDocumentError("invalid_rank_status", "Unknown track cannot have a rank or tier.")
        status = raw_status or ("ranked" if values.get("global_rank") is not None or values.get("tier") is not None else "unknown")
        normalized.append(NormalizedKaggleTrack(track, status, values, frozenset(values)))
    return NormalizedKaggleProfile(parsed.username, parsed.observed_at, parsed.source, tuple(normalized))
