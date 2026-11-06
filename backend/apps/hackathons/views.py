from django.db import IntegrityError, connection, transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import BooleanField, Count, F, IntegerField, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce, Lower
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from apps.hackathons.models import (
    HackathonAchievement, HackathonEvent, HackathonParticipation,
    HackathonProject, HackathonSubmission,
)
from apps.hackathons.overview import build_hackathon_overview
from apps.hackathons.serializers import (
    AchievementSerializer, EntrySerializer, EventSerializer, ParticipationSerializer,
    ProjectSerializer, SubmissionSerializer, model_errors,
)


class HackathonPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def choice_filter(request, name, choices):
    value = request.query_params.get(name, "")
    if value and value not in choices:
        raise ValidationError({name: f"Choose one of: {', '.join(choices)}."})
    return value


def bounded_text_filter(request, name, limit=100):
    value = request.query_params.get(name, "").strip()
    if len(value) > limit:
        raise ValidationError({name: f"Use at most {limit} characters."})
    return value


def technology_match(term):
    """Exact case-insensitive JSON-array member check on supported databases."""
    column = '"hackathons_hackathonproject"."technologies"'
    if connection.vendor == "postgresql":
        sql = f"EXISTS (SELECT 1 FROM jsonb_array_elements_text({column}) AS tech(value) WHERE LOWER(tech.value) = LOWER(%s))"
    elif connection.vendor == "sqlite":
        sql = f"EXISTS (SELECT 1 FROM json_each({column}) WHERE LOWER(json_each.value) = LOWER(%s))"
    else:
        raise ValidationError({"technology": "Technology filtering is unavailable on this database."})
    return RawSQL(sql, [term], output_field=BooleanField())


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


def lock_deletion_context(instance):
    """Freeze child links before checking achievement verification status.

    Always lock from parent to child: event -> participation -> submission ->
    achievement, or project -> submission -> achievement. This matches the
    update path's parent-before-achievement order.
    """
    if isinstance(instance, HackathonEvent):
        list(HackathonParticipation.objects.filter(event_id=instance.pk).order_by("pk").select_for_update().values_list("pk", flat=True))
        list(HackathonSubmission.objects.filter(event_id=instance.pk).order_by("pk").select_for_update().values_list("pk", flat=True))
    elif isinstance(instance, HackathonProject):
        list(HackathonSubmission.objects.filter(project_id=instance.pk).order_by("pk").select_for_update().values_list("pk", flat=True))


class ManualViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = HackathonPagination

    def set_visibility(self, request, pk):
        if not isinstance(request.data, dict) or set(request.data) != {"is_public"}:
            raise ValidationError({"is_public": "Provide only the is_public Boolean field."})
        if type(request.data["is_public"]) is not bool:
            raise ValidationError({"is_public": "Use a JSON Boolean."})
        with transaction.atomic():
            instance = get_object_or_404(self.get_queryset().select_for_update(), pk=pk)
            if instance.is_public != request.data["is_public"]:
                instance.is_public = request.data["is_public"]
                instance.save(update_fields=("is_public", "updated_at"))
            return Response({"id": instance.pk, "is_public": instance.is_public})

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

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            # Resolve ownership first. Participation deletion also takes the
            # event lock, so concurrent event deletion follows the same order.
            instance = self.get_object()
            if isinstance(instance, HackathonParticipation):
                HackathonEvent.objects.select_for_update().get(pk=instance.event_id)
            instance = type(instance).objects.select_for_update().get(pk=instance.pk)
            lock_deletion_context(instance)
            if isinstance(instance, HackathonAchievement):
                verified = instance.verification_status == HackathonAchievement.VerificationStatus.VERIFIED
            else:
                statuses = list(
                    context_achievements(instance)
                    .order_by("pk")
                    .select_for_update(of=("self",))
                    .values_list("verification_status", flat=True)
                )
                verified = HackathonAchievement.VerificationStatus.VERIFIED in statuses
            if verified:
                raise PermissionDenied("Verified achievements are read-only in manual management.")
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
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
        if self.action != "list":
            return qs
        state = choice_filter(self.request, "status", HackathonParticipation.Status.values)
        if state:
            qs = qs.filter(participations__user=self.request.user, participations__status=state)
        year = self.request.query_params.get("year")
        if year:
            if len(year) > 4 or not year.isdigit() or not (1 <= int(year) <= 9999):
                raise ValidationError({"year": "Enter a valid year."})
            qs = qs.filter(start_date__year=int(year))
        name = bounded_text_filter(self.request, "name")
        if name:
            qs = qs.filter(name__icontains=name)
        # DRF reserves the `format` query parameter for renderer selection.
        event_format = choice_filter(self.request, "event_format", HackathonEvent.Format.values)
        source = choice_filter(self.request, "source", HackathonEvent.Source.values)
        if event_format:
            qs = qs.filter(format=event_format)
        if source:
            qs = qs.filter(source=source)
        ordering = choice_filter(self.request, "ordering", ("newest", "oldest", "date_newest", "date_oldest", "name_asc"))
        order = {
            "newest": ("-created_at", "-pk"), "oldest": ("created_at", "pk"),
            "date_newest": (F("start_date").desc(nulls_last=True), "-pk"),
            "date_oldest": (F("start_date").asc(nulls_last=True), "pk"),
            "name_asc": (Lower("name").asc(), "pk"),
        }
        return qs.order_by(*order[ordering or "newest"])

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, source="manual", external_id="")


class ProjectViewSet(ManualViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        related_count = (HackathonSubmission.objects.filter(project_id=OuterRef("pk"), owner=self.request.user)
                         .values("project_id").annotate(total=Count("event_id", distinct=True)).values("total")[:1])
        qs = HackathonProject.objects.filter(owner=self.request.user).annotate(
            related_hackathon_count=Coalesce(Subquery(related_count, output_field=IntegerField()), Value(0))
        )
        if self.action != "list":
            return qs.order_by("-created_at", "-pk")
        title = bounded_text_filter(self.request, "title")
        search = bounded_text_filter(self.request, "search")
        technology = bounded_text_filter(self.request, "technology")
        source = choice_filter(self.request, "source", HackathonProject.Source.values)
        visibility = choice_filter(self.request, "visibility", ("public", "private"))
        ordering = choice_filter(self.request, "ordering", ("newest", "oldest", "recently_updated", "title_asc", "title_desc"))
        if title:
            qs = qs.filter(title__icontains=title)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if source:
            qs = qs.filter(source=source)
        if visibility:
            qs = qs.filter(is_public=visibility == "public")
        if technology:
            qs = qs.annotate(_technology_match=technology_match(technology)).filter(_technology_match=True)
        order = {
            "newest": ("-created_at", "-pk"), "oldest": ("created_at", "pk"),
            "recently_updated": ("-updated_at", "-pk"), "title_asc": (Lower("title").asc(), "pk"),
            "title_desc": (Lower("title").desc(), "-pk"),
        }
        return qs.order_by(*order[ordering or "newest"])

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, source="manual", external_id="")

    @action(detail=True, methods=["patch"], url_path="visibility")
    def visibility(self, request, pk=None):
        return self.set_visibility(request, pk)


class ParticipationViewSet(ManualViewSet):
    serializer_class = ParticipationSerializer

    def get_queryset(self):
        return HackathonParticipation.objects.filter(user=self.request.user).select_related("event").order_by("-created_at", "-pk")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["patch"], url_path="visibility")
    def visibility(self, request, pk=None):
        return self.set_visibility(request, pk)


class SubmissionViewSet(ManualViewSet):
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        return HackathonSubmission.objects.filter(owner=self.request.user).select_related("project", "event").order_by("-created_at", "-pk")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, source="manual", external_id="")


class AchievementViewSet(ManualViewSet):
    serializer_class = AchievementSerializer

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
        return Response(build_hackathon_overview(request.user), status=status.HTTP_200_OK)
