from typing import Any


def map_codeforces_user_to_snapshot(raw_user: dict[str, Any]) -> dict[str, Any]:
    first_name = (raw_user.get("firstName") or "").strip()
    last_name = (raw_user.get("lastName") or "").strip()
    display_name = " ".join(part for part in [first_name, last_name] if part)
    if not display_name:
        display_name = raw_user.get("handle")

    return {
        "display_name": display_name,
        "headline_rank_title": raw_user.get("rank"),
        "rating": raw_user.get("rating"),
        "highest_rating": raw_user.get("maxRating"),
        "contests_count": None,
        "solved_count": None,
        "avatar_url": raw_user.get("titlePhoto") or raw_user.get("avatar"),
        "metadata_json": {"raw_profile": raw_user},
    }
