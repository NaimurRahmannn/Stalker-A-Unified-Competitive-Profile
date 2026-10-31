from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from apps.hackathons.models import (
    HackathonAchievement, HackathonEvent, HackathonParticipation,
    HackathonProject, HackathonSubmission,
)
from apps.hackathons.serializers import (
    AchievementSerializer, EntrySerializer, EventSerializer, ParticipationSerializer,
    ProjectSerializer, SubmissionSerializer, model_errors,
)


class HackathonPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def context_achievements(instance):
    """Achievements whose verified meaning depends on this record."""
    queryset = HackathonAchievement.objects.all()
    if isinstance(instance, HackathonEvent):
        return queryset.filter(participation__event_id=instance.pk)
    if isinstance(instance, HackathonParticipation):
        return queryset.filter(participation_id=instance.pk)
    if isinstance(instance, HackathonSubmission):
        return queryset.filter(submission_id=instance.pk)
    if isinstance(instance, HackathonProject):
        return queryset.filter(submission__project_id=instance.pk)
    return queryset.filter(pk=instance.pk)


class ManualViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HackathonPagination

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        with transaction.atomic():
            # Resolve through the owner-scoped queryset, then lock the current
            # record and all achievements whose verification it could affect.
            instance = self.get_object()
            instance = type(instance).objects.select_for_update().get(pk=instance.pk)
            statuses = list(
                context_achievements(instance)
                .order_by("pk")
                .select_for_update(of=("self",))
                .values_list("verification_status", flat=True)
            )
            if HackathonAchievement.VerificationStatus.VERIFIED in statuses:
                raise PermissionDenied("This record is read-only while a verified achievement depends on it.")
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, "_prefetched_objects_cache", None):
                instance._prefetched_objects_cache = {}
            return Response(serializer.data)

    def perform_update(self, serializer):
        if hasattr(serializer.instance, "source") and serializer.instance.source != "manual":
            raise PermissionDenied("Imported records are read-only in manual management.")
        serializer.save()

    def perform_destroy(self, instance):
        verified = HackathonAchievement.VerificationStatus.VERIFIED
        if (
            isinstance(instance, HackathonAchievement) and instance.verification_status == verified
            or isinstance(instance, HackathonEvent) and HackathonAchievement.objects.filter(participation__event=instance, verification_status=verified).exists()
            or isinstance(instance, HackathonParticipation) and instance.achievements.filter(verification_status=verified).exists()
            or isinstance(instance, HackathonSubmission) and instance.achievements.filter(verification_status=verified).exists()
            or isinstance(instance, HackathonProject) and HackathonAchievement.objects.filter(submission__project=instance, verification_status=verified).exists()
        ):
            raise PermissionDenied("Verified achievements are read-only in manual management.")
        if hasattr(instance, "source") and instance.source != "manual":
            raise PermissionDenied("Imported records cannot be deleted here.")
        if isinstance(instance, HackathonEvent) and (
            instance.participations.exclude(user=self.request.user).exists()
            or instance.submissions.exclude(owner=self.request.user).exists()
        ):
            raise PermissionDenied("This event has records owned by another user.")
        if isinstance(instance, HackathonProject) and instance.submissions.exclude(owner=self.request.user).exists():
            raise PermissionDenied("This project has submissions owned by another user.")
        if isinstance(instance, HackathonEvent) and instance.submissions.exclude(source="manual").exists():
            raise PermissionDenied("This event contains imported submissions.")
        if isinstance(instance, HackathonProject) and instance.submissions.exclude(source="manual").exists():
            raise PermissionDenied("This project contains imported submissions.")
        if isinstance(instance, HackathonParticipation) and instance.event.submissions.exclude(source="manual").exists():
            raise PermissionDenied("This participation is linked to imported submissions.")
        instance.delete()


class EventViewSet(ManualViewSet):
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = HackathonEvent.objects.filter(owner=self.request.user).order_by("-created_at", "-pk")
        if self.action in ("list", "retrieve"):
            qs = qs.prefetch_related(
                Prefetch("participations", queryset=HackathonParticipation.objects.filter(user=self.request.user).prefetch_related("achievements")),
                Prefetch("submissions", queryset=HackathonSubmission.objects.filter(owner=self.request.user).select_related("project")),
            )
        state = self.request.query_params.get("status")
        if state in HackathonParticipation.Status.values:
            qs = qs.filter(participations__user=self.request.user, participations__status=state)
        year = self.request.query_params.get("year")
        if year:
            if not year.isdigit() or not (1 <= int(year) <= 9999):
                raise ValidationError({"year": "Enter a valid year."})
            qs = qs.filter(start_date__year=int(year))
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name[:100])
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, source="manual", external_id="")


class ProjectViewSet(ManualViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = HackathonProject.objects.filter(owner=self.request.user).order_by("-created_at", "-pk")
        title = self.request.query_params.get("title")
        return qs.filter(title__icontains=title[:100]) if title else qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, source="manual", external_id="")


class ParticipationViewSet(ManualViewSet):
    serializer_class = ParticipationSerializer

    def get_queryset(self):
        return HackathonParticipation.objects.filter(user=self.request.user).select_related("event").order_by("-created_at", "-pk")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SubmissionViewSet(ManualViewSet):
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        return HackathonSubmission.objects.filter(owner=self.request.user).select_related("project", "event").order_by("-created_at", "-pk")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, source="manual", external_id="")


class AchievementViewSet(ManualViewSet):
    serializer_class = AchievementSerializer

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            locked = HackathonAchievement.objects.select_for_update().get(pk=instance.pk)
            if locked.verification_status == HackathonAchievement.VerificationStatus.VERIFIED:
                raise PermissionDenied("Verified achievements are read-only in manual management.")
            return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        qs = HackathonAchievement.objects.filter(participation__user=self.request.user).select_related("participation", "submission").order_by("-created_at", "-pk")
        kind = self.request.query_params.get("achievement_type")
        return qs.filter(achievement_type=kind) if kind in HackathonAchievement.AchievementType.values else qs

    def perform_create(self, serializer):
        serializer.save(verification_status=HackathonAchievement.VerificationStatus.SELF_REPORTED)


class ManualEntryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EntrySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            with transaction.atomic():
                if "event_id" in data:
                    event = data["event_id"]
                else:
                    event = HackathonEvent.objects.create(owner=request.user, source="manual", external_id="", **data["event"])

                existing = HackathonParticipation.objects.filter(user=request.user, event=event).first()
                if existing:
                    # Explicit event selection permits reuse, but never overwrites status or visibility.
                    if "event_id" not in data or any(getattr(existing, key) != value for key, value in data["participation"].items()):
                        raise ValidationError({"participation": "Participation already exists. Edit it separately, or submit matching details."})
                    participation = existing
                else:
                    participation = HackathonParticipation.objects.create(user=request.user, event=event, **data["participation"])

                project = data.get("project_id")
                if "project" in data:
                    project = HackathonProject.objects.create(owner=request.user, source="manual", external_id="", **data["project"])
                submission = None
                if project:
                    if HackathonSubmission.objects.filter(event=event, project=project).exists():
                        raise ValidationError({"project_id": "This project already has a submission for the event."})
                    submission = HackathonSubmission.objects.create(owner=request.user, event=event, project=project, source="manual", external_id="", **data["submission"])

                achievements = []
                for item in data.get("achievements", []):
                    item = dict(item)
                    link = item.pop("link_submission", False)
                    if link and not submission:
                        raise ValidationError({"achievements": "A linked submission requires a project in this entry."})
                    achievements.append(HackathonAchievement.objects.create(
                        participation=participation,
                        submission=submission if link else None,
                        verification_status=HackathonAchievement.VerificationStatus.SELF_REPORTED,
                        **item,
                    ))
        except DjangoValidationError as exc:
            raise ValidationError(model_errors(exc)) from exc
        except IntegrityError as exc:
            raise ValidationError({"non_field_errors": ["A conflicting record already exists."]}) from exc

        return Response({
            "event_id": event.pk,
            "participation_id": participation.pk,
            "project_id": project.pk if project else None,
            "submission_id": submission.pk if submission else None,
            "achievement_ids": [item.pk for item in achievements],
        }, status=status.HTTP_201_CREATED)


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
