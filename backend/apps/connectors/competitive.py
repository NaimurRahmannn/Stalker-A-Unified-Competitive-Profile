from django.utils.dateparse import parse_datetime

from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    CodeforcesStats,
    LeetCodeStats,
    PlatformAccount,
)
from apps.connectors.providers.atcoder.mapper import get_atcoder_rating_color

SUPPORTED_PLATFORMS = (
    PlatformAccount.Platform.CODEFORCES,
    PlatformAccount.Platform.ATCODER,
    PlatformAccount.Platform.LEETCODE,
)
RECENT_ACTIVITY_LIMIT = 20


def build_competitive_programming_overview(
    user,
    *,
    include_activity: bool = True,
) -> dict:
    accounts = {
        account.platform: account
        for account in PlatformAccount.objects.filter(
            user=user,
            platform__in=SUPPORTED_PLATFORMS,
        ).select_related("codeforces_stats", "atcoder_stats", "leetcode_stats")
    }
    platforms = [
        _platform_summary(platform, accounts.get(platform))
        for platform in SUPPORTED_PLATFORMS
    ]
    connected = [platform for platform in platforms if platform["connected"]]

    solved_count = sum(
        platform["solved_count"] or 0 for platform in connected
    )
    contest_count = sum(
        platform["contest_count"] or 0 for platform in connected
    )
    accepted_count = sum(
        platform["accepted_submission_count"] or 0
        for platform in connected
    )

    payload = {
        "summary": {
            "active_platforms": len(connected),
            "solved_count": solved_count,
            "solved_count_complete": all(
                platform["solved_count_complete"] for platform in connected
            ),
            "contest_count": contest_count,
            "contest_count_complete": all(
                platform["contest_count"] is not None for platform in connected
            ),
            "accepted_submission_count": accepted_count,
            "accepted_submission_count_complete": all(
                platform["accepted_submission_count_complete"]
                for platform in connected
            ),
        },
        "platforms": platforms,
    }
    if include_activity:
        payload["recent_activity"] = _recent_activity(accounts)
    return payload


def _platform_summary(platform: str, account: PlatformAccount | None) -> dict:
    base = {
        "platform": platform,
        "connected": account is not None,
        "account_id": account.pk if account else None,
        "handle": account.handle if account else None,
        "profile_url": account.profile_url if account else None,
        "rating": None,
        "max_rating": None,
        "rank": None,
        "solved_count": None,
        "solved_count_complete": account is None,
        "contest_count": None,
        "contest_label": (
            "Contests" if platform == PlatformAccount.Platform.CODEFORCES
            else "Rated contests"
        ),
        "accepted_submission_count": None,
        "accepted_submission_count_complete": account is None,
        "problem_breakdown": None,
        "data_updated_at": None,
    }
    if account is None:
        return base

    if platform == PlatformAccount.Platform.CODEFORCES:
        try:
            stats = account.codeforces_stats
        except CodeforcesStats.DoesNotExist:
            return base
        base.update(
            {
                "rating": stats.rating,
                "max_rating": stats.max_rating,
                "rank": stats.rank,
                "solved_count": stats.solved_count,
                "solved_count_complete": True,
                "contest_count": stats.contest_count,
                "accepted_submission_count": stats.accepted_submission_count,
                "accepted_submission_count_complete": True,
                "data_updated_at": stats.updated_at,
            }
        )
        return base

    if platform == PlatformAccount.Platform.ATCODER:
        try:
            stats = account.atcoder_stats
        except AtCoderStats.DoesNotExist:
            return base
        base.update(
            {
                "rating": stats.current_rating,
                "max_rating": stats.max_rating,
                "rank": get_atcoder_rating_color(stats.current_rating),
                "solved_count": stats.solved_count,
                "solved_count_complete": stats.submission_backfill_complete,
                "contest_count": stats.rated_contest_count,
                "accepted_submission_count": stats.accepted_submission_count,
                "accepted_submission_count_complete": (
                    stats.submission_backfill_complete
                ),
                "data_updated_at": max(
                    filter(
                        None,
                        (
                            stats.rating_data_updated_at,
                            stats.submission_data_updated_at,
                        ),
                    ),
                    default=None,
                ),
            }
        )
        return base

    try:
        stats = account.leetcode_stats
    except LeetCodeStats.DoesNotExist:
        return base
    base.update(
        {
            "rating": stats.current_contest_rating,
            "solved_count": stats.solved_total,
            "solved_count_complete": stats.problem_stats_complete,
            "contest_count": stats.attended_contest_count,
            "problem_breakdown": {
                "easy": stats.solved_easy,
                "medium": stats.solved_medium,
                "hard": stats.solved_hard,
            },
            "data_updated_at": stats.data_updated_at,
        }
    )
    return base


def _recent_activity(accounts: dict[str, PlatformAccount]) -> list[dict]:
    activity = []
    codeforces = accounts.get(PlatformAccount.Platform.CODEFORCES)
    if codeforces is not None:
        try:
            stats = codeforces.codeforces_stats
        except CodeforcesStats.DoesNotExist:
            stats = None
        if stats is not None:
            events = (
                stats.recent_activity
                if isinstance(stats.recent_activity, list)
                else []
            )
            for index, event in enumerate(events):
                if not isinstance(event, dict):
                    continue
                occurred_at = event.get("submitted_at")
                if not isinstance(occurred_at, str) or parse_datetime(
                    occurred_at
                ) is None:
                    continue
                submission_id = event.get("submission_id")
                problem_index = event.get("problem_index")
                problem_name = event.get("problem_name") or "Submission"
                title = (
                    f"{problem_index}. {problem_name}"
                    if problem_index
                    else problem_name
                )
                activity.append(
                    {
                        "id": (
                            f"codeforces-{submission_id}"
                            if submission_id is not None
                            else f"codeforces-{occurred_at}-{index}"
                        ),
                        "platform": PlatformAccount.Platform.CODEFORCES,
                        "type": (
                            "problem_solved"
                            if event.get("verdict") == "OK"
                            else "submission"
                        ),
                        "title": title,
                        "subtitle": event.get("language"),
                        "verdict": event.get("verdict"),
                        "accepted": event.get("verdict") == "OK",
                        "rating_change": None,
                        "occurred_at": occurred_at,
                    }
                )

    atcoder = accounts.get(PlatformAccount.Platform.ATCODER)
    if atcoder is not None:
        submissions = AtCoderSubmission.objects.filter(
            platform_account=atcoder
        ).order_by("-submitted_at", "-external_submission_id")[
            :RECENT_ACTIVITY_LIMIT
        ]
        for submission in submissions:
            activity.append(
                {
                    "id": f"atcoder-{submission.external_submission_id}",
                    "platform": PlatformAccount.Platform.ATCODER,
                    "type": (
                        "problem_solved"
                        if submission.verdict == "AC"
                        else "submission"
                    ),
                    "title": submission.external_problem_id,
                    "subtitle": submission.language,
                    "verdict": submission.verdict,
                    "accepted": submission.verdict == "AC",
                    "rating_change": None,
                    "occurred_at": submission.submitted_at.isoformat(),
                }
            )

    activity.sort(
        key=lambda event: (
            parse_datetime(event["occurred_at"]),
            event["platform"],
            event["id"],
        ),
        reverse=True,
    )
    return activity[:RECENT_ACTIVITY_LIMIT]
