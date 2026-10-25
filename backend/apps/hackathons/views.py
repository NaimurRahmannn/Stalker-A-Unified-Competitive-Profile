from django.db.models import Count, Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.hackathons.models import (
    HackathonAchievement,
    HackathonParticipation,
    HackathonProject,
)


class HackathonOverviewView(APIView):
    """Return an authenticated user's hackathon activity summary.

    Definitions:
    - hackathons_attended: distinct events with participation status
      ``attended`` or ``submitted``.
    - projects_submitted: distinct projects having at least one submission
      with status ``submitted``.
    - achievements_recorded: all achievement records regardless of
      verification state.
    - placements_recorded: achievements of type ``placement`` with a
      non-null rank.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        hackathons_attended = (
            HackathonParticipation.objects.filter(
                user=user,
                status__in=[
                    HackathonParticipation.Status.ATTENDED,
                    HackathonParticipation.Status.SUBMITTED,
                ],
            )
            .values("event")
            .distinct()
            .count()
        )

        projects_submitted = (
            HackathonProject.objects.filter(
                owner=user,
                submissions__status="submitted",
            )
            .distinct()
            .count()
        )

        achievements_qs = HackathonAchievement.objects.filter(
            participation__user=user,
        )
        achievements_recorded = achievements_qs.count()
        placements_recorded = achievements_qs.filter(
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            rank__isnull=False,
        ).count()

        return Response(
            {
                "hackathons_attended": hackathons_attended,
                "projects_submitted": projects_submitted,
                "achievements_recorded": achievements_recorded,
                "placements_recorded": placements_recorded,
            },
            status=status.HTTP_200_OK,
        )
