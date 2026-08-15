from datetime import datetime
from typing import Any

from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmissionSyncState,
    AtCoderSyncState,
)

RECENT_ACTIVITY_LIMIT = 20
SNAPSHOT_LIMIT = 180


def build_atcoder_sync_summary(
    stats: AtCoderStats | None,
    sync_state: AtCoderSyncState | None,
    submission_state: AtCoderSubmissionSyncState | None,
) -> dict[str, Any]:
    rating_freshness = stats.rating_data_updated_at if stats else None
    submission_freshness = stats.submission_data_updated_at if stats else None

    if sync_state is None:
        rating_status = "success" if rating_freshness else "never"
        submission_status = "success" if submission_freshness else "never"
        if rating_freshness and submission_freshness:
            overall_status = "success"
        elif rating_freshness or submission_freshness:
            overall_status = "partial"
        else:
            overall_status = "never_synced"
        rating_error = None
        submission_error = None
        rating_attempted_at = None
        submission_attempted_at = None
    else:
        overall_status = (
            "never_synced"
            if sync_state.overall_status == AtCoderSyncState.OverallStatus.NEVER
            else sync_state.overall_status
        )
        rating_status = sync_state.rating_status
        submission_status = sync_state.submission_status
        rating_error = sync_state.rating_error_code or None
        submission_error = sync_state.submission_error_code or None
        rating_attempted_at = sync_state.rating_sync_attempted_at
        submission_attempted_at = sync_state.submission_sync_attempted_at

    progress_status = _submission_progress_status(stats, submission_state)
    progress_error = (
        submission_state.blocked_reason
        if submission_state and submission_state.blocked_reason
        else None
    )

    return {
        "status": overall_status,
        "rating": {
            "status": rating_status,
            "updated_at": rating_freshness,
            "attempted_at": rating_attempted_at,
            "using_cached_data": _uses_cached_data(
                rating_status,
                rating_freshness,
            ),
            "error_code": rating_error,
        },
        "submissions": {
            "status": submission_status,
            "updated_at": submission_freshness,
            "attempted_at": submission_attempted_at,
            "using_cached_data": _uses_cached_data(
                submission_status,
                submission_freshness,
            ),
            "error_code": submission_error or progress_error,
            "progress": {
                "status": progress_status,
                "stats_complete": bool(
                    stats and stats.submission_backfill_complete
                ),
                "error_code": progress_error,
            },
        },
    }


def _submission_progress_status(
    stats: AtCoderStats | None,
    submission_state: AtCoderSubmissionSyncState | None,
) -> str:
    if submission_state is not None:
        return submission_state.progress_status
    if stats and stats.submission_backfill_complete:
        return AtCoderSubmissionSyncState.ProgressStatus.CAUGHT_UP
    if stats and stats.submission_data_updated_at:
        return AtCoderSubmissionSyncState.ProgressStatus.BACKFILLING
    return "not_started"


def _uses_cached_data(status: str, freshness: datetime | None) -> bool:
    return freshness is not None and status in {
        AtCoderSyncState.SourceStatus.FAILED,
        AtCoderSyncState.SourceStatus.BLOCKED,
        AtCoderSyncState.SourceStatus.SKIPPED_FRESH,
        AtCoderSyncState.SourceStatus.DISABLED,
    }
