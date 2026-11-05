"""Owner-scoped, privacy-filtered Hackathon data for public profiles."""

from urllib.parse import urlsplit

from django.db.models import Count, F, Prefetch, Q
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination

from apps.hackathons.models import (
    HackathonAchievement, HackathonParticipation, HackathonProject,
    HackathonSubmission,
)


def safe_public_url(value):
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password:
            return value
    except ValueError:
        pass
    return None


def public_projects(user):
    return HackathonProject.objects.filter(owner=user, is_public=True)


def public_participations(user):
    return HackathonParticipation.objects.filter(user=user, is_public=True, event__owner=user)


def public_achievements(user):
    return HackathonAchievement.objects.filter(
        participation__user=user, participation__is_public=True,
        participation__event__owner=user,
    ).filter(
        Q(submission__isnull=True) |
        Q(submission__owner=user, submission__project__owner=user,
          submission__project__is_public=True, submission__event__owner=user,
          submission__event_id=F("participation__event_id"))
    )


def public_submissions(user):
    return HackathonSubmission.objects.filter(
        owner=user, project__owner=user, project__is_public=True,
        event__owner=user, event__participations__user=user,
        event__participations__is_public=True,
        status=HackathonSubmission.Status.SUBMITTED,
    )


def public_project_cards(user):
    return public_projects(user).prefetch_related(Prefetch(
        "submissions",
        queryset=public_submissions(user).select_related("event").order_by("-created_at", "-pk")[:5],
        to_attr="public_submission_preview",
    ))


def hackathon_summary(user):
    achievement_counts = public_achievements(user).aggregate(
        total=Count("pk"),
        verified=Count("pk", filter=Q(verification_status=HackathonAchievement.VerificationStatus.VERIFIED)),
    )
    return {
        "published_projects": public_projects(user).count(),
        "public_participations": public_participations(user).count(),
        "public_achievements": achievement_counts["total"],
        "verified_achievements": achievement_counts["verified"],
    }


class PublicHackathonProjectSerializer(serializers.ModelSerializer):
    associations = serializers.SerializerMethodField()
    project_url = serializers.SerializerMethodField()
    repository_url = serializers.SerializerMethodField()
    demo_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HackathonProject
        fields = ("id", "title", "description", "technologies", "source", "associations", "project_url",
                  "repository_url", "demo_url", "video_url", "image_url")

    def get_associations(self, obj):
        return [{"event_id": row.event_id, "event_name": row.event.name,
                 "event_url": safe_public_url(row.event.event_url)}
                for row in obj.public_submission_preview]

    def get_project_url(self, obj):
        return safe_public_url(obj.project_url)

    def get_repository_url(self, obj):
        return safe_public_url(obj.repository_url)

    def get_demo_url(self, obj):
        return safe_public_url(obj.demo_url)

    def get_video_url(self, obj):
        return safe_public_url(obj.video_url)

    def get_image_url(self, obj):
        return safe_public_url(obj.image_url)


class PublicHackathonParticipationSerializer(serializers.ModelSerializer):
    event = serializers.SerializerMethodField()

    class Meta:
        model = HackathonParticipation
        fields = ("id", "event", "status", "team_name", "role")

    def get_event(self, obj):
        event = obj.event
        return {"id": event.pk, "name": event.name, "organizer": event.organizer,
                "start_date": event.start_date, "end_date": event.end_date,
                "format": event.format, "event_url": safe_public_url(event.event_url)}


class PublicHackathonAchievementSerializer(serializers.ModelSerializer):
    project_id = serializers.SerializerMethodField()

    class Meta:
        model = HackathonAchievement
        fields = ("id", "participation_id", "project_id", "achievement_type", "title",
                  "rank", "total_participants", "description", "verification_status")

    def get_project_id(self, obj):
        return obj.submission.project_id if obj.submission_id else None


class PublicHackathonSubmissionSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source="event.name")
    event_url = serializers.SerializerMethodField()
    project_title = serializers.CharField(source="project.title")
    submission_url = serializers.SerializerMethodField()

    class Meta:
        model = HackathonSubmission
        fields = ("id", "project_id", "project_title", "event_id", "event_name", "event_url", "submission_url")

    def get_event_url(self, obj):
        return safe_public_url(obj.event.event_url)

    def get_submission_url(self, obj):
        return safe_public_url(obj.submission_url)


class PublicHackathonPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 20


def paginated_public_collection(request, queryset, serializer_class, page_param):
    paginator = PublicHackathonPagination()
    paginator.page_query_param = page_param
    page = paginator.paginate_queryset(queryset.order_by("-created_at", "-pk"), request)
    return paginator.get_paginated_response(serializer_class(page, many=True).data).data
