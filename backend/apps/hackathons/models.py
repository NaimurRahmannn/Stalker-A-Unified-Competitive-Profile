from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class HackathonEvent(models.Model):
    """Represent a hackathon event recorded for a STALKER user.

    Events are owner-scoped: different users may independently record the same
    real-world hackathon without merging.  Global canonicalization is deferred.

    Ownership is immutable after creation to prevent orphaning or misattributing
    existing participations and submissions.
    """

    class Format(models.TextChoices):
        ONLINE = "online", "Online"
        IN_PERSON = "in_person", "In-Person"
        HYBRID = "hybrid", "Hybrid"
        UNKNOWN = "unknown", "Unknown"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        DEVPOST = "devpost", "Devpost"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hackathon_events",
    )
    name = models.CharField(max_length=500)
    organizer = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    event_url = models.URLField(max_length=500, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    format = models.CharField(
        max_length=20,
        choices=Format.choices,
        default=Format.UNKNOWN,
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    external_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Prevent duplicate imported events per owner+source, but only
            # when external_id is non-empty.  Manual events (empty
            # external_id) are always permitted to have duplicate names.
            models.UniqueConstraint(
                fields=["owner", "source", "external_id"],
                name="unique_hackathon_event_external_id",
                condition=~models.Q(external_id=""),
            ),
            models.CheckConstraint(
                condition=models.Q(start_date__isnull=True)
                | models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=models.F("start_date")),
                name="hack_event_date_order_chk",
            ),
        ]
        indexes = [
            models.Index(
                fields=["owner", "-created_at"],
                name="hack_event_owner_idx",
            ),
            models.Index(
                fields=["owner", "source", "external_id"],
                name="hack_event_ext_idx",
            ),
        ]

    def clean(self):
        # Name cannot be empty or pure whitespace
        if self.name is not None:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Event name cannot be blank."})

        # Ownership immutability: owner cannot be changed once created.
        if self.pk:
            orig = (
                HackathonEvent.objects.filter(pk=self.pk)
                .values("owner_id")
                .first()
            )
            if orig and orig["owner_id"] != self.owner_id:
                raise ValidationError(
                    {"owner": "Event owner cannot be changed once created."}
                )

        if (
            self.start_date
            and self.end_date
            and self.end_date < self.start_date
        ):
            raise ValidationError(
                {"end_date": "End date cannot precede start date."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.owner.username})"


class HackathonProject(models.Model):
    """Store projects created by hackathon participants.

    A project is not tied directly to an event; the relationship is expressed
    through ``HackathonSubmission``.  A project can be submitted to multiple
    events.

    Ownership is immutable after creation to preserve submission integrity.
    """

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        DEVPOST = "devpost", "Devpost"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hackathon_projects",
    )
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    repository_url = models.URLField(max_length=500, blank=True)
    demo_url = models.URLField(max_length=500, blank=True)
    video_url = models.URLField(max_length=500, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    technologies = models.JSONField(default=list, blank=True)
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    external_id = models.CharField(max_length=255, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "source", "external_id"],
                name="unique_hackathon_project_external_id",
                condition=~models.Q(external_id=""),
            ),
        ]
        indexes = [
            models.Index(
                fields=["owner", "-created_at"],
                name="hack_project_owner_idx",
            ),
            models.Index(
                fields=["owner", "source", "external_id"],
                name="hack_project_ext_idx",
            ),
        ]

    def clean(self):
        # Title cannot be empty or pure whitespace
        if self.title is not None:
            self.title = self.title.strip()
        if not self.title:
            raise ValidationError({"title": "Project title cannot be blank."})

        # Ownership immutability: owner cannot be changed once created.
        if self.pk:
            orig = (
                HackathonProject.objects.filter(pk=self.pk)
                .values("owner_id")
                .first()
            )
            if orig and orig["owner_id"] != self.owner_id:
                raise ValidationError(
                    {"owner": "Project owner cannot be changed once created."}
                )

        if not isinstance(self.technologies, list):
            raise ValidationError(
                {"technologies": "Technologies must be a list of strings."}
            )
        if not all(isinstance(t, str) for t in self.technologies):
            raise ValidationError(
                {"technologies": "Each technology must be a string."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} ({self.owner.username})"


class HackathonSubmission(models.Model):
    """Represent a specific project being submitted to a particular hackathon.

    Ownership invariant: ``owner``, ``project.owner``, and ``event.owner`` must
    all be the same user.  Owner, project, and event references are immutable
    after creation.

    External deduplication: For imported records (e.g. Devpost), external_id
    is unique per (owner, source) at the database level across all events,
    preventing duplicate imported submissions even across concurrent writes or
    bulk inserts, while allowing distinct users to record shared submissions.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        WITHDRAWN = "withdrawn", "Withdrawn"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        DEVPOST = "devpost", "Devpost"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hackathon_submissions",
    )
    project = models.ForeignKey(
        "hackathons.HackathonProject",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    event = models.ForeignKey(
        "hackathons.HackathonEvent",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    submission_url = models.URLField(max_length=500, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    external_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "event"],
                name="unique_hackathon_submission_project_event",
            ),
            # Database-enforced uniqueness: an imported submission is unique
            # per owner, source, and external_id (scoped to the user, not global)
            models.UniqueConstraint(
                fields=["owner", "source", "external_id"],
                name="unique_hack_sub_owner_ext_id",
                condition=~models.Q(external_id=""),
            ),
        ]
        indexes = [
            models.Index(
                fields=["owner", "-created_at"],
                name="hack_sub_owner_idx",
            ),
            models.Index(
                fields=["event", "-created_at"],
                name="hack_submission_event_idx",
            ),
            models.Index(
                fields=["owner", "source", "external_id"],
                name="hack_sub_owner_ext_idx",
            ),
        ]

    def clean(self):
        # Auto-populate owner from project or event if not set
        if not self.owner_id:
            if self.project_id:
                self.owner_id = (
                    self.project.owner_id
                    if hasattr(self, "_project_cache")
                    or HackathonProject.objects.filter(pk=self.project_id).exists()
                    else None
                )
            elif self.event_id:
                self.owner_id = (
                    self.event.owner_id
                    if hasattr(self, "_event_cache")
                    or HackathonEvent.objects.filter(pk=self.event_id).exists()
                    else None
                )

        # Relationship immutability: owner, project, and event cannot change once created.
        if self.pk:
            orig = (
                HackathonSubmission.objects.filter(pk=self.pk)
                .values("owner_id", "project_id", "event_id")
                .first()
            )
            if orig:
                if orig["owner_id"] != self.owner_id:
                    raise ValidationError(
                        {"owner": "Submission owner cannot be changed once created."}
                    )
                if orig["project_id"] != self.project_id:
                    raise ValidationError(
                        {"project": "Submission project cannot be changed once created."}
                    )
                if orig["event_id"] != self.event_id:
                    raise ValidationError(
                        {"event": "Submission event cannot be changed once created."}
                    )

        # Cross-table ownership check: project and event must belong to the same user.
        project_owner_id = None
        event_owner_id = None
        if self.project_id:
            project_owner_id = (
                self.project.owner_id
                if hasattr(self, "_project_cache")
                or HackathonProject.objects.filter(pk=self.project_id).exists()
                else None
            )
        if self.event_id:
            event_owner_id = (
                self.event.owner_id
                if hasattr(self, "_event_cache")
                or HackathonEvent.objects.filter(pk=self.event_id).exists()
                else None
            )

        if (
            project_owner_id is not None
            and event_owner_id is not None
            and project_owner_id != event_owner_id
        ):
            raise ValidationError(
                "Project and event must belong to the same user."
            )

        if self.owner_id:
            if project_owner_id is not None and self.owner_id != project_owner_id:
                raise ValidationError(
                    {"owner": "Submission owner must match project owner."}
                )
            if event_owner_id is not None and self.owner_id != event_owner_id:
                raise ValidationError(
                    {"owner": "Submission owner must match event owner."}
                )

    def save(self, *args, **kwargs):
        # Ensure owner is populated before full_clean runs
        if not self.owner_id:
            if self.project_id:
                self.owner_id = (
                    self.project.owner_id
                    if hasattr(self, "_project_cache")
                    or HackathonProject.objects.filter(pk=self.project_id).exists()
                    else None
                )
            elif self.event_id:
                self.owner_id = (
                    self.event.owner_id
                    if hasattr(self, "_event_cache")
                    or HackathonEvent.objects.filter(pk=self.event_id).exists()
                    else None
                )
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Submission: {self.project} → {self.event}"


class HackathonParticipation(models.Model):
    """Represent a user's participation in a hackathon.

    Ownership invariant: ``event.owner`` must equal ``user``.
    Both user and event references are immutable after creation.
    """

    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        ATTENDED = "attended", "Attended"
        SUBMITTED = "submitted", "Submitted"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hackathon_participations",
    )
    event = models.ForeignKey(
        "hackathons.HackathonEvent",
        on_delete=models.CASCADE,
        related_name="participations",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REGISTERED,
    )
    team_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=100, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"],
                name="unique_hackathon_participation",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "-created_at"],
                name="hack_part_user_idx",
            ),
        ]

    def clean(self):
        # Relationship immutability: user and event cannot change once created.
        if self.pk:
            orig = (
                HackathonParticipation.objects.filter(pk=self.pk)
                .values("user_id", "event_id")
                .first()
            )
            if orig:
                if orig["user_id"] != self.user_id:
                    raise ValidationError(
                        {"user": "Participation user cannot be changed once created."}
                    )
                if orig["event_id"] != self.event_id:
                    raise ValidationError(
                        {"event": "Participation event cannot be changed once created."}
                    )

        if self.event_id and self.user_id:
            event_owner_id = (
                self.event.owner_id
                if hasattr(self, "_event_cache")
                or HackathonEvent.objects.filter(pk=self.event_id).exists()
                else None
            )
            if (
                event_owner_id is not None
                and event_owner_id != self.user_id
            ):
                raise ValidationError(
                    "Participation event must belong to the participant."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.event.name}"


class HackathonAchievement(models.Model):
    """Store user-entered hackathon achievements and placements.

    Achievements are self-reported by default.  Users must not be able to
    set their own achievements to ``verified`` through public APIs; that
    transition is reserved for admin or a future verification workflow.

    Participation reference is immutable after creation.

    If a ``submission`` is linked, its event must match the participation
    event and the submission must belong to the same user.
    """

    class AchievementType(models.TextChoices):
        PLACEMENT = "placement", "Placement"
        AWARD = "award", "Award"
        FINALIST = "finalist", "Finalist"
        PARTICIPATION = "participation", "Participation"
        OTHER = "other", "Other"

    class VerificationStatus(models.TextChoices):
        SELF_REPORTED = "self_reported", "Self-Reported"
        EVIDENCE_PROVIDED = "evidence_provided", "Evidence Provided"
        VERIFIED = "verified", "Verified"

    participation = models.ForeignKey(
        "hackathons.HackathonParticipation",
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    submission = models.ForeignKey(
        "hackathons.HackathonSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="achievements",
    )
    achievement_type = models.CharField(
        max_length=20,
        choices=AchievementType.choices,
    )
    title = models.CharField(max_length=500)
    rank = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    total_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    description = models.TextField(blank=True)
    evidence_url = models.URLField(max_length=500, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.SELF_REPORTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rank__isnull=True) | models.Q(rank__gte=1),
                name="hack_achieve_rank_gte_1_chk",
            ),
            models.CheckConstraint(
                condition=models.Q(total_participants__isnull=True)
                | models.Q(total_participants__gte=1),
                name="hack_achieve_total_gte_1_chk",
            ),
            models.CheckConstraint(
                condition=models.Q(rank__isnull=True)
                | models.Q(total_participants__isnull=True)
                | models.Q(rank__lte=models.F("total_participants")),
                name="hack_achieve_rank_lte_total_chk",
            ),
        ]
        indexes = [
            models.Index(
                fields=["participation", "-created_at"],
                name="hack_achieve_part_idx",
            ),
        ]

    def clean(self):
        # Title cannot be empty or pure whitespace
        if self.title is not None:
            self.title = self.title.strip()
        if not self.title:
            raise ValidationError({"title": "Achievement title cannot be blank."})

        # Participation reference is immutable after creation
        if self.pk:
            orig = (
                HackathonAchievement.objects.filter(pk=self.pk)
                .values("participation_id")
                .first()
            )
            if orig and orig["participation_id"] != self.participation_id:
                raise ValidationError(
                    {"participation": "Achievement participation cannot be changed once created."}
                )

        # Rank must be ≥ 1
        if self.rank is not None and self.rank < 1:
            raise ValidationError(
                {"rank": "Rank must be at least 1."}
            )
        if self.total_participants is not None and self.total_participants < 1:
            raise ValidationError(
                {"total_participants": "Total participants must be at least 1."}
            )
        # Rank cannot exceed total_participants.
        if (
            self.rank is not None
            and self.total_participants is not None
            and self.rank > self.total_participants
        ):
            raise ValidationError(
                {"rank": "Rank cannot exceed total participants."}
            )
        # Cross-table: submission event must match participation event, and
        # the submission's project must belong to the same user.
        if self.submission_id and self.participation_id:
            try:
                submission = (
                    self.submission
                    if hasattr(self, "_submission_cache")
                    else HackathonSubmission.objects.select_related(
                        "event", "project"
                    ).get(pk=self.submission_id)
                )
                participation = (
                    self.participation
                    if hasattr(self, "_participation_cache")
                    else HackathonParticipation.objects.get(
                        pk=self.participation_id
                    )
                )
            except (
                HackathonSubmission.DoesNotExist,
                HackathonParticipation.DoesNotExist,
            ):
                return  # FK integrity will catch missing rows

            if submission.event_id != participation.event_id:
                raise ValidationError(
                    "Achievement submission must belong to the same event "
                    "as the participation."
                )
            if submission.project.owner_id != participation.user_id:
                raise ValidationError(
                    "Achievement submission must belong to the same user "
                    "as the participation."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.title} ({self.get_achievement_type_display()})"
