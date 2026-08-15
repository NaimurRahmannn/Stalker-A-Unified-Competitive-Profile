import type {
  AtCoderAnalyticsResponse,
  CodeforcesAnalyticsResponse,
  CompetitiveActivity,
  CompetitiveOverviewResponse,
  RatingChartPoint,
} from "./types";

export function codeforcesRatingPoints(
  analytics: CodeforcesAnalyticsResponse,
): RatingChartPoint[] {
  return analytics.rating_history.map((event) => ({
    contestId: String(event.contest_id ?? event.timestamp),
    contestName: event.contest_name ?? "Rated contest",
    rating: event.new_rating,
    ratingChange: event.rating_change,
    occurredAt: event.timestamp,
  }));
}

export function overviewActivity(
  overview: CompetitiveOverviewResponse,
): CompetitiveActivity[] {
  return overview.recent_activity.map((event) => ({
    id: event.id,
    platform: event.platform,
    type: event.type,
    title: event.title,
    subtitle: event.subtitle,
    verdict: event.verdict,
    accepted: event.accepted,
    ratingChange: event.rating_change,
    occurredAt: event.occurred_at,
  }));
}

export function atcoderRatingPoints(
  analytics: AtCoderAnalyticsResponse,
): RatingChartPoint[] {
  return analytics.rating_history.flatMap((event) =>
    event.new_rating === null
      ? []
      : [{
          contestId: event.contest_id,
          contestName: event.contest_name ?? event.contest_id,
          rating: event.new_rating,
          ratingChange: event.rating_change,
          performance: event.performance,
          occurredAt: event.occurred_at,
        }],
  );
}

export function codeforcesActivity(
  analytics: CodeforcesAnalyticsResponse,
): CompetitiveActivity[] {
  return analytics.recent_activity.map((event, index) => ({
    id: `codeforces-${event.submission_id ?? `${event.submitted_at}-${index}`}`,
    platform: "codeforces",
    type: event.verdict === "OK" ? "problem_solved" : "submission",
    title: `${event.problem_index ? `${event.problem_index}. ` : ""}${event.problem_name}`,
    subtitle: [event.problem_rating === null ? null : `Rating ${event.problem_rating}`, event.language].filter(Boolean).join(" · ") || null,
    verdict: event.verdict,
    accepted: event.verdict === "OK",
    ratingChange: null,
    occurredAt: event.submitted_at,
  }));
}

export function atcoderActivity(
  analytics: AtCoderAnalyticsResponse,
): CompetitiveActivity[] {
  return analytics.recent_activity.map((event) => ({
    id: `atcoder-${event.submission_id}`,
    platform: "atcoder",
    type: event.accepted ? "problem_solved" : "submission",
    title: event.problem_id,
    subtitle: event.language,
    verdict: event.verdict,
    accepted: event.accepted,
    ratingChange: null,
    occurredAt: event.submitted_at,
  }));
}
