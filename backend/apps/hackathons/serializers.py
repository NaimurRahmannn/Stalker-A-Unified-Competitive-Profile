"""Manual-only API serializers. Imported core records remain read-only here."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from urllib.parse import urlsplit
from rest_framework import serializers

from apps.hackathons.models import (
    HackathonAchievement, HackathonEvent, HackathonParticipation,
    HackathonProject, HackathonSubmission,
)


def model_errors(exc):
    if hasattr(exc, "message_dict"):
        return exc.message_dict
    return {"non_field_errors": exc.messages}


class HttpUrlField(serializers.URLField):
    """Accept only web URLs in user-managed manual records."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value and urlsplit(value).scheme.lower() not in {"http", "https"}:
            raise serializers.ValidationError("Enter an HTTP(S) URL.")
        return value


class OwnedRelatedField(serializers.PrimaryKeyRelatedField):
    """Resolve IDs only among objects belonging to the current user."""

    def get_queryset(self):
        model = self.queryset.model
        user = self.context["request"].user
        if model is HackathonParticipation:
            return self.queryset.filter(user=user)
        if model is HackathonAchievement:
            return self.queryset.filter(participation__user=user)
        return self.queryset.filter(owner=user)


class ManualSerializer(serializers.ModelSerializer):
    writable = ()
    immutable = ()

    def validate(self, attrs):
        raw = getattr(self, "initial_data", None)
        if raw is None and self.parent is not None:
            raw = self.parent.initial_data.get(self.field_name, {})
        supplied = set(raw or {})
        forbidden = supplied - set(self.writable)
        if forbidden:
            raise serializers.ValidationError({key: "This field cannot be set here." for key in sorted(forbidden)})
        if self.instance and any(key in supplied for key in self.immutable):
            raise serializers.ValidationError({key: "This relationship is immutable." for key in self.immutable if key in supplied})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(model_errors(exc)) from exc
        except IntegrityError as exc:
            raise serializers.ValidationError({"non_field_errors": ["A conflicting record already exists."]}) from exc

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                return super().update(instance, validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(model_errors(exc)) from exc
        except IntegrityError as exc:
            raise serializers.ValidationError({"non_field_errors": ["A conflicting record already exists."]}) from exc


class EventSerializer(ManualSerializer):
    writable = ("name", "organizer", "description", "event_url", "start_date", "end_date", "format")
    event_url = HttpUrlField(max_length=500, allow_blank=True, required=False)
    participation = serializers.SerializerMethodField()
    submissions = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = HackathonEvent
        fields = ("id", "name", "organizer", "description", "event_url", "start_date", "end_date", "format", "source", "external_id", "created_at", "updated_at", "participation", "submissions", "achievements")
        read_only_fields = ("id", "source", "external_id", "created_at", "updated_at")

    def get_participation(self, obj):
        items = list(obj.participations.all())
        return ParticipationSerializer(items[0], context=self.context).data if items else None

    def get_submissions(self, obj):
        return SubmissionSerializer(obj.submissions.all(), many=True, context=self.context).data

    def get_achievements(self, obj):
        items = list(obj.participations.all())
        return AchievementSerializer(items[0].achievements.all(), many=True, context=self.context).data if items else []

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start = attrs.get("start_date", self.instance.start_date if self.instance else None)
        end = attrs.get("end_date", self.instance.end_date if self.instance else None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot precede start date."})
        return attrs


class ProjectSerializer(ManualSerializer):
    writable = ("title", "description", "repository_url", "demo_url", "video_url", "image_url", "technologies", "is_public")
    technologies = serializers.ListField(child=serializers.CharField(), required=False)
    repository_url = HttpUrlField(max_length=500, allow_blank=True, required=False)
    demo_url = HttpUrlField(max_length=500, allow_blank=True, required=False)
    video_url = HttpUrlField(max_length=500, allow_blank=True, required=False)
    image_url = HttpUrlField(max_length=500, allow_blank=True, required=False)

    class Meta:
        model = HackathonProject
        fields = ("id", "title", "description", "repository_url", "demo_url", "video_url", "image_url", "technologies", "is_public", "source", "external_id", "created_at", "updated_at")
        read_only_fields = ("id", "source", "external_id", "created_at", "updated_at")


class ParticipationSerializer(ManualSerializer):
    writable = ("event", "status", "team_name", "role", "is_public")
    immutable = ("event",)
    event = OwnedRelatedField(queryset=HackathonEvent.objects.all())

    class Meta:
        model = HackathonParticipation
        fields = ("id", "event", "status", "team_name", "role", "is_public", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not self.instance and HackathonParticipation.objects.filter(user=self.context["request"].user, event=attrs.get("event")).exists():
            raise serializers.ValidationError({"event": "Participation already exists for this event."})
        return attrs


class SubmissionSerializer(ManualSerializer):
    writable = ("event", "project", "status", "submission_url", "submitted_at")
    immutable = ("event", "project")
    event = OwnedRelatedField(queryset=HackathonEvent.objects.all())
    project = OwnedRelatedField(queryset=HackathonProject.objects.all())
    project_title = serializers.CharField(source="project.title", read_only=True)
    submission_url = HttpUrlField(max_length=500, allow_blank=True, required=False)

    class Meta:
        model = HackathonSubmission
        fields = ("id", "event", "project", "status", "submission_url", "submitted_at", "project_title", "source", "external_id", "created_at", "updated_at")
        read_only_fields = ("id", "project_title", "source", "external_id", "created_at", "updated_at")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not self.instance and HackathonSubmission.objects.filter(event=attrs.get("event"), project=attrs.get("project")).exists():
            raise serializers.ValidationError({"project": "This project already has a submission for the event."})
        return attrs


class AchievementSerializer(ManualSerializer):
    writable = ("participation", "submission", "achievement_type", "title", "rank", "total_participants", "description", "evidence_url")
    immutable = ("participation",)
    participation = OwnedRelatedField(queryset=HackathonParticipation.objects.all())
    submission = OwnedRelatedField(queryset=HackathonSubmission.objects.all(), required=False, allow_null=True)
    evidence_url = HttpUrlField(max_length=500, allow_blank=True, required=False)

    class Meta:
        model = HackathonAchievement
        fields = ("id", "participation", "submission", "achievement_type", "title", "rank", "total_participants", "description", "evidence_url", "verification_status", "created_at", "updated_at")
        read_only_fields = ("id", "verification_status", "created_at", "updated_at")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        participation = attrs.get("participation", self.instance.participation if self.instance else None)
        submission = attrs.get("submission", self.instance.submission if self.instance else None)
        rank = attrs.get("rank", self.instance.rank if self.instance else None)
        total = attrs.get("total_participants", self.instance.total_participants if self.instance else None)
        if rank is not None and total is not None and rank > total:
            raise serializers.ValidationError({"rank": "Rank cannot exceed total participants."})
        if submission and participation and (submission.event_id != participation.event_id or submission.owner_id != participation.user_id):
            raise serializers.ValidationError({"submission": "Submission must belong to this participation's event and user."})
        return attrs


class EntryParticipationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=HackathonParticipation.Status.choices, required=False)
    team_name = serializers.CharField(max_length=255, allow_blank=True, required=False)
    role = serializers.CharField(max_length=100, allow_blank=True, required=False)
    is_public = serializers.BooleanField(required=False)


class EntrySubmissionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=HackathonSubmission.Status.choices, required=False)
    submission_url = HttpUrlField(max_length=500, allow_blank=True, required=False)
    submitted_at = serializers.DateTimeField(allow_null=True, required=False)


class EntryAchievementSerializer(serializers.Serializer):
    achievement_type = serializers.ChoiceField(choices=HackathonAchievement.AchievementType.choices)
    title = serializers.CharField(max_length=500, allow_blank=False, trim_whitespace=True)
    rank = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    total_participants = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    evidence_url = HttpUrlField(max_length=500, allow_blank=True, required=False)
    link_submission = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if set(getattr(self, "initial_data", {})) - set(self.fields):
            raise serializers.ValidationError("Unsupported achievement field.")
        if attrs.get("rank") is not None and attrs.get("total_participants") is not None and attrs["rank"] > attrs["total_participants"]:
            raise serializers.ValidationError({"rank": "Rank cannot exceed total participants."})
        return attrs


class EntrySerializer(serializers.Serializer):
    event_id = OwnedRelatedField(queryset=HackathonEvent.objects.all(), required=False)
    event = EventSerializer(required=False)
    participation = EntryParticipationSerializer()
    project_id = OwnedRelatedField(queryset=HackathonProject.objects.all(), required=False)
    project = ProjectSerializer(required=False)
    submission = EntrySubmissionSerializer(required=False)
    achievements = EntryAchievementSerializer(many=True, required=False)

    def validate(self, attrs):
        keys = set(self.initial_data)
        if keys - set(self.fields):
            raise serializers.ValidationError({key: "Unknown field." for key in keys - set(self.fields)})
        nested_allowed = {
            "participation": set(EntryParticipationSerializer().fields),
            "submission": set(EntrySubmissionSerializer().fields),
            "achievements": set(EntryAchievementSerializer().fields),
        }
        for name in ("participation", "submission"):
            if name in self.initial_data and set(self.initial_data[name]) - nested_allowed[name]:
                raise serializers.ValidationError({name: "Unsupported or protected field."})
        for item in self.initial_data.get("achievements", []):
            if set(item) - nested_allowed["achievements"]:
                raise serializers.ValidationError({"achievements": "Unsupported or protected field."})
        if ("event_id" in attrs) == ("event" in attrs):
            raise serializers.ValidationError({"event": "Provide exactly one of event or event_id."})
        if "project_id" in attrs and "project" in attrs:
            raise serializers.ValidationError({"project": "Provide either project or project_id."})
        has_project = "project_id" in attrs or "project" in attrs
        if has_project != ("submission" in attrs):
            raise serializers.ValidationError({"submission": "A project and submission must be provided together."})
        return attrs
