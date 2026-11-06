"""Owner-scoped Hackathon totals shared by management and dashboard APIs."""

from apps.hackathons.models import (
    HackathonAchievement, HackathonParticipation, HackathonProject,
)


def build_hackathon_overview(user):
    """Count attended events, submitted projects, and recorded achievements."""
    achievements = HackathonAchievement.objects.filter(participation__user=user)
    return {
        "hackathons_attended": (
            HackathonParticipation.objects.filter(
                user=user,
                status__in=[
                    HackathonParticipation.Status.ATTENDED,
                    HackathonParticipation.Status.SUBMITTED,
                ],
            ).values("event").distinct().count()
        ),
        "projects_submitted": (
            HackathonProject.objects.filter(
                owner=user, submissions__status="submitted",
            ).distinct().count()
        ),
        "achievements_recorded": achievements.count(),
        "placements_recorded": achievements.filter(
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            rank__isnull=False,
        ).count(),
    }
