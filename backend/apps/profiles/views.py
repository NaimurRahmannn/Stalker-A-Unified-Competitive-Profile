from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.connectors.competitive import build_competitive_programming_overview
from apps.connectors.models import PlatformAccount
from apps.datathons.overview import build_kaggle_overview
from apps.profiles.serializers import (
    PublicProfilePlatformSerializer,
    PublicProfileUserSerializer,
)
from apps.profiles.hackathon_public import (
    PublicHackathonAchievementSerializer, PublicHackathonParticipationSerializer,
    PublicHackathonProjectSerializer, PublicHackathonSubmissionSerializer,
    hackathon_summary, paginated_public_collection, public_achievements,
    public_participations, public_project_cards, public_submissions,
)


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username: str):
        user = get_object_or_404(User, username=username)
        platforms = (
            PlatformAccount.objects.filter(user=user)
            .select_related("codeforces_stats", "atcoder_stats", "leetcode_stats", "ctf_team_profile", "kaggle_profile_link__kaggle_profile")
            .prefetch_related("ctf_team_profile__yearly_rankings", "kaggle_manual_stats", "kaggle_profile_link__kaggle_profile__track_stats")
            .order_by("platform")
        )

        return Response(
            {
                "user": PublicProfileUserSerializer(user).data,
                "platforms": PublicProfilePlatformSerializer(
                    platforms,
                    many=True,
                ).data,
                "competitive_programming": build_competitive_programming_overview(
                    user,
                    include_activity=False,
                ),
                "hackathons": hackathon_summary(user),
                "datathons": build_kaggle_overview(user),
            }
        )


class PublicHackathonPortfolioView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username: str):
        user = get_object_or_404(User, username=username)
        return Response({
            "summary": hackathon_summary(user),
            "projects": paginated_public_collection(request, public_project_cards(user), PublicHackathonProjectSerializer, "projects_page"),
            "participations": paginated_public_collection(request, public_participations(user).select_related("event"), PublicHackathonParticipationSerializer, "participations_page"),
            "achievements": paginated_public_collection(request, public_achievements(user).select_related("submission"), PublicHackathonAchievementSerializer, "achievements_page"),
            "submissions": paginated_public_collection(request, public_submissions(user).select_related("project", "event"), PublicHackathonSubmissionSerializer, "submissions_page"),
        })


class PublicHackathonProjectDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username: str, project_id: int):
        user = get_object_or_404(User, username=username)
        project = get_object_or_404(public_project_cards(user), pk=project_id)
        submissions = public_submissions(user).filter(project_id=project.pk).select_related("project", "event").order_by("-created_at", "-pk")
        achievements = public_achievements(user).filter(submission__project_id=project.pk).select_related("submission").order_by("-created_at", "-pk")
        return Response({
            "project": PublicHackathonProjectSerializer(project).data,
            "submission_count": submissions.count(),
            "submissions": PublicHackathonSubmissionSerializer(submissions[:20], many=True).data,
            "achievement_count": achievements.count(),
            "achievements": PublicHackathonAchievementSerializer(achievements[:20], many=True).data,
        })


PublicProfileAPIView = PublicProfileView
