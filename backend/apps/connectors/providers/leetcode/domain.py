from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class LeetCodeProfileData:
    handle: str
    profile_url: str
    display_name: str | None
    avatar_url: str | None
    country: str | None
    organization: str | None
    school: str | None
    global_problem_ranking: int | None
    reputation: int | None


@dataclass(frozen=True, slots=True)
class LeetCodeProblemStatsData:
    solved_total: int
    solved_easy: int
    solved_medium: int
    solved_hard: int
    stats_complete: bool


@dataclass(frozen=True, slots=True)
class LeetCodeContestStatsData:
    current_rating: float | None
    attended_contest_count: int
    global_ranking: int | None
    total_participants: int | None
    top_percentage: float | None


@dataclass(frozen=True, slots=True)
class LeetCodeRatingEventData:
    contest_title: str
    occurred_at: datetime
    rating: float
    ranking: int | None
    problems_solved: int | None
    total_problems: int | None
    finish_time_seconds: int | None
    attended: bool

