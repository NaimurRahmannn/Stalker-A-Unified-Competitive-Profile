"""Tests for the hackathons app — Phase 1 and Review Corrections.

Covers:
- Model creation, validation, full_clean lifecycle
- Ownership and relationship immutability protections
- Database check constraints (date order, rank bounds)
- Imported identity and submission deduplication
- Cross-user data isolation
- Django admin configuration
- Authenticated overview API endpoint
"""

import datetime

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.hackathons.admin import (
    HackathonAchievementAdmin,
    HackathonEventAdmin,
    HackathonParticipationAdmin,
    HackathonProjectAdmin,
    HackathonSubmissionAdmin,
)
from apps.hackathons.models import (
    HackathonAchievement,
    HackathonEvent,
    HackathonParticipation,
    HackathonProject,
    HackathonSubmission,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(username="alice", email="alice@example.com"):
    return User.objects.create_user(
        username=username, email=email, password="password123"
    )


def _create_event(owner, name="HackFest 2025", **kwargs):
    return HackathonEvent.objects.create(owner=owner, name=name, **kwargs)


def _create_project(owner, title="My Project", **kwargs):
    return HackathonProject.objects.create(owner=owner, title=title, **kwargs)


def _create_submission(project, event, **kwargs):
    return HackathonSubmission.objects.create(
        project=project, event=event, **kwargs
    )


def _create_participation(user, event, **kwargs):
    return HackathonParticipation.objects.create(
        user=user, event=event, **kwargs
    )


# ===================================================================
# MODEL TESTS: HackathonEvent
# ===================================================================


class HackathonEventModelTests(APITestCase):
    """Tests for HackathonEvent creation, validation, constraints, and immutability."""

    def setUp(self):
        self.user = _create_user()

    def test_create_event_successfully(self):
        event = _create_event(self.user)
        self.assertEqual(event.name, "HackFest 2025")
        self.assertEqual(event.owner, self.user)
        self.assertEqual(event.source, HackathonEvent.Source.MANUAL)
        self.assertEqual(event.format, HackathonEvent.Format.UNKNOWN)
        self.assertIsNotNone(event.created_at)

    def test_str_representation(self):
        event = _create_event(self.user, name="DemoDay")
        self.assertEqual(str(event), f"DemoDay ({self.user.username})")

    def test_duplicate_manual_event_names_permitted(self):
        _create_event(self.user, name="Same Name")
        event2 = _create_event(self.user, name="Same Name")
        self.assertIsNotNone(event2.pk)

    def test_end_date_before_start_date_rejected_by_validation(self):
        event = HackathonEvent(
            owner=self.user,
            name="Bad Dates",
            start_date=datetime.date(2025, 6, 15),
            end_date=datetime.date(2025, 6, 10),
        )
        with self.assertRaises(ValidationError):
            event.save()

    def test_valid_date_range_accepted(self):
        event = _create_event(
            self.user,
            start_date=datetime.date(2025, 6, 10),
            end_date=datetime.date(2025, 6, 15),
        )
        self.assertEqual(event.start_date, datetime.date(2025, 6, 10))

    def test_nullable_dates_accepted(self):
        event = _create_event(self.user)
        self.assertIsNone(event.start_date)
        self.assertIsNone(event.end_date)

    def test_single_start_date_accepted(self):
        event = _create_event(self.user, start_date=datetime.date(2025, 6, 10))
        self.assertIsNotNone(event.pk)
        self.assertIsNone(event.end_date)

    def test_single_end_date_accepted(self):
        event = _create_event(self.user, end_date=datetime.date(2025, 6, 10))
        self.assertIsNotNone(event.pk)
        self.assertIsNone(event.start_date)

    def test_duplicate_external_id_same_source_rejected(self):
        _create_event(
            self.user,
            source=HackathonEvent.Source.DEVPOST,
            external_id="devpost-123",
        )
        with self.assertRaises((ValidationError, IntegrityError)):
            _create_event(
                self.user,
                source=HackathonEvent.Source.DEVPOST,
                external_id="devpost-123",
            )

    def test_empty_external_id_duplicates_allowed(self):
        _create_event(self.user, external_id="")
        event2 = _create_event(self.user, external_id="")
        self.assertIsNotNone(event2.pk)

    def test_same_external_id_different_users_allowed(self):
        user2 = _create_user("bob", "bob@example.com")
        _create_event(
            self.user,
            source=HackathonEvent.Source.DEVPOST,
            external_id="devpost-123",
        )
        event2 = _create_event(
            user2,
            source=HackathonEvent.Source.DEVPOST,
            external_id="devpost-123",
        )
        self.assertIsNotNone(event2.pk)

    def test_empty_name_rejected_on_save(self):
        event = HackathonEvent(owner=self.user, name="")
        with self.assertRaises(ValidationError):
            event.save()

    def test_whitespace_name_rejected_on_save(self):
        event = HackathonEvent(owner=self.user, name="   ")
        with self.assertRaises(ValidationError):
            event.save()

    def test_invalid_url_rejected_on_save(self):
        event = HackathonEvent(
            owner=self.user, name="Valid", event_url="not-a-url"
        )
        with self.assertRaises(ValidationError):
            event.save()

    def test_invalid_format_choice_rejected_on_save(self):
        event = HackathonEvent(
            owner=self.user, name="Valid", format="invalid_format"
        )
        with self.assertRaises(ValidationError):
            event.save()

    def test_changing_event_owner_rejected(self):
        """Blocker 1: Changing an event's owner after creation must be rejected."""
        event = _create_event(self.user)
        user2 = _create_user("bob", "bob@example.com")
        _create_participation(self.user, event)

        event.owner = user2
        with self.assertRaises(ValidationError) as ctx:
            event.save()
        self.assertIn("owner", ctx.exception.message_dict)

        event.refresh_from_db()
        self.assertEqual(event.owner, self.user)

    def test_invalid_dates_rejected_by_database_constraint(self):
        """Blocker 2: Database CheckConstraint must reject end_date < start_date
        even when model validation is bypassed via bulk_create."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HackathonEvent.objects.bulk_create([
                    HackathonEvent(
                        owner=self.user,
                        name="Bad Dates Direct DB",
                        start_date=datetime.date(2025, 6, 15),
                        end_date=datetime.date(2025, 6, 10),
                    )
                ])

    def test_cascade_delete_with_owner(self):
        _create_event(self.user)
        self.user.delete()
        self.assertEqual(HackathonEvent.objects.count(), 0)


# ===================================================================
# MODEL TESTS: HackathonProject
# ===================================================================


class HackathonProjectModelTests(APITestCase):

    def setUp(self):
        self.user = _create_user()

    def test_create_project_successfully(self):
        project = _create_project(self.user, technologies=["Python", "React"])
        self.assertEqual(project.title, "My Project")
        self.assertEqual(project.technologies, ["Python", "React"])
        self.assertFalse(project.is_public)

    def test_str_representation(self):
        project = _create_project(self.user, title="Cool App")
        self.assertEqual(str(project), f"Cool App ({self.user.username})")

    def test_empty_title_rejected_on_save(self):
        project = HackathonProject(owner=self.user, title="")
        with self.assertRaises(ValidationError):
            project.save()

    def test_whitespace_title_rejected_on_save(self):
        project = HackathonProject(owner=self.user, title="   ")
        with self.assertRaises(ValidationError):
            project.save()

    def test_invalid_repository_url_rejected_on_save(self):
        project = HackathonProject(
            owner=self.user, title="Project", repository_url="ftp://invalid url"
        )
        with self.assertRaises(ValidationError):
            project.save()

    def test_technologies_must_be_list_of_strings(self):
        project = HackathonProject(
            owner=self.user,
            title="Bad Tech",
            technologies={"key": "value"},
        )
        with self.assertRaises(ValidationError):
            project.save()

    def test_technologies_non_string_elements_rejected(self):
        project = HackathonProject(
            owner=self.user,
            title="Bad Tech",
            technologies=["Python", 42],
        )
        with self.assertRaises(ValidationError):
            project.save()

    def test_duplicate_external_id_rejected(self):
        _create_project(
            self.user,
            source=HackathonProject.Source.DEVPOST,
            external_id="dp-proj-1",
        )
        with self.assertRaises((ValidationError, IntegrityError)):
            _create_project(
                self.user,
                source=HackathonProject.Source.DEVPOST,
                external_id="dp-proj-1",
            )

    def test_empty_external_id_duplicates_allowed(self):
        _create_project(self.user, external_id="")
        p2 = _create_project(self.user, title="Another", external_id="")
        self.assertIsNotNone(p2.pk)

    def test_changing_project_owner_rejected(self):
        """Blocker 1: Changing a project's owner after creation must be rejected."""
        project = _create_project(self.user)
        user2 = _create_user("bob", "bob@example.com")
        event = _create_event(self.user)
        _create_submission(project, event)

        project.owner = user2
        with self.assertRaises(ValidationError) as ctx:
            project.save()
        self.assertIn("owner", ctx.exception.message_dict)

        project.refresh_from_db()
        self.assertEqual(project.owner, self.user)

    def test_cascade_delete_with_owner(self):
        _create_project(self.user)
        self.user.delete()
        self.assertEqual(HackathonProject.objects.count(), 0)


# ===================================================================
# MODEL TESTS: HackathonSubmission
# ===================================================================


class HackathonSubmissionModelTests(APITestCase):

    def setUp(self):
        self.user = _create_user()
        self.event = _create_event(self.user)
        self.project = _create_project(self.user)

    def test_create_submission_successfully(self):
        sub = _create_submission(self.project, self.event)
        self.assertEqual(sub.status, HackathonSubmission.Status.DRAFT)
        self.assertEqual(sub.project, self.project)
        self.assertEqual(sub.event, self.event)

    def test_project_submitted_to_multiple_events(self):
        event2 = _create_event(self.user, name="HackFest 2026")
        sub1 = _create_submission(self.project, self.event)
        sub2 = _create_submission(self.project, event2)
        self.assertNotEqual(sub1.pk, sub2.pk)

    def test_duplicate_project_event_rejected(self):
        _create_submission(self.project, self.event)
        with self.assertRaises((ValidationError, IntegrityError)):
            _create_submission(self.project, self.event)

    def test_duplicate_project_event_rejected_by_database_constraint(self):
        _create_submission(self.project, self.event)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HackathonSubmission.objects.bulk_create([
                    HackathonSubmission(project=self.project, event=self.event)
                ])

    def test_cross_user_submission_rejected(self):
        user2 = _create_user("bob", "bob@example.com")
        other_event = _create_event(user2, name="Bob's Event")
        sub = HackathonSubmission(
            project=self.project,
            event=other_event,
        )
        with self.assertRaises(ValidationError):
            sub.save()

    def test_invalid_status_choice_rejected_on_save(self):
        sub = HackathonSubmission(
            project=self.project,
            event=self.event,
            status="invalid_status",
        )
        with self.assertRaises(ValidationError):
            sub.save()

    def test_changing_submission_event_rejected(self):
        """Blocker 1: Changing a submission's event after creation must be rejected."""
        sub = _create_submission(self.project, self.event)
        event2 = _create_event(self.user, name="Event 2")

        sub.event = event2
        with self.assertRaises(ValidationError) as ctx:
            sub.save()
        self.assertIn("event", ctx.exception.message_dict)

        sub.refresh_from_db()
        self.assertEqual(sub.event, self.event)

    def test_changing_submission_project_rejected(self):
        """Blocker 1: Changing a submission's project after creation must be rejected."""
        sub = _create_submission(self.project, self.event)
        project2 = _create_project(self.user, title="Project 2")

        sub.project = project2
        with self.assertRaises(ValidationError) as ctx:
            sub.save()
        self.assertIn("project", ctx.exception.message_dict)

        sub.refresh_from_db()
        self.assertEqual(sub.project, self.project)

    def test_imported_submission_deduplication_per_event_and_user(self):
        """Section 2: Deduplicating imported submissions per (event, source, external_id)."""
        _create_submission(
            self.project,
            self.event,
            source=HackathonSubmission.Source.DEVPOST,
            external_id="devpost-sub-101",
        )
        # Same event, same external_id, different project is rejected
        proj2 = _create_project(self.user, title="Alt Project")
        sub2 = HackathonSubmission(
            project=proj2,
            event=self.event,
            source=HackathonSubmission.Source.DEVPOST,
            external_id="devpost-sub-101",
        )
        with self.assertRaises((ValidationError, IntegrityError)):
            sub2.save()

    def test_imported_submission_deduplication_database_constraint(self):
        """Section 2: Database UniqueConstraint rejects duplicate (event, source, external_id)."""
        _create_submission(
            self.project,
            self.event,
            source=HackathonSubmission.Source.DEVPOST,
            external_id="devpost-sub-101",
        )
        proj2 = _create_project(self.user, title="Alt Project")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HackathonSubmission.objects.bulk_create([
                    HackathonSubmission(
                        project=proj2,
                        event=self.event,
                        source=HackathonSubmission.Source.DEVPOST,
                        external_id="devpost-sub-101",
                    )
                ])

    def test_imported_submission_different_users_allowed(self):
        """Different users can record the same external submission ID in their own events."""
        user2 = _create_user("bob", "bob@example.com")
        event2 = _create_event(user2, name="Bob's Event")
        proj2 = _create_project(user2, title="Bob's Project")

        _create_submission(
            self.project,
            self.event,
            source=HackathonSubmission.Source.DEVPOST,
            external_id="devpost-sub-shared",
        )
        sub2 = _create_submission(
            proj2,
            event2,
            source=HackathonSubmission.Source.DEVPOST,
            external_id="devpost-sub-shared",
        )
        self.assertIsNotNone(sub2.pk)

    def test_str_representation(self):
        sub = _create_submission(self.project, self.event)
        self.assertIn("Submission:", str(sub))

    def test_cascade_delete_project(self):
        _create_submission(self.project, self.event)
        self.project.delete()
        self.assertEqual(HackathonSubmission.objects.count(), 0)

    def test_cascade_delete_event(self):
        _create_submission(self.project, self.event)
        self.event.delete()
        self.assertEqual(HackathonSubmission.objects.count(), 0)


# ===================================================================
# MODEL TESTS: HackathonParticipation
# ===================================================================


class HackathonParticipationModelTests(APITestCase):

    def setUp(self):
        self.user = _create_user()
        self.event = _create_event(self.user)

    def test_create_participation_successfully(self):
        part = _create_participation(self.user, self.event)
        self.assertEqual(part.status, HackathonParticipation.Status.REGISTERED)
        self.assertEqual(part.user, self.user)

    def test_participation_without_project(self):
        part = _create_participation(self.user, self.event)
        self.assertIsNotNone(part.pk)
        self.assertEqual(HackathonProject.objects.count(), 0)

    def test_duplicate_participation_rejected(self):
        _create_participation(self.user, self.event)
        with self.assertRaises((ValidationError, IntegrityError)):
            _create_participation(self.user, self.event)

    def test_duplicate_participation_rejected_by_database_constraint(self):
        _create_participation(self.user, self.event)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HackathonParticipation.objects.bulk_create([
                    HackathonParticipation(user=self.user, event=self.event)
                ])

    def test_cross_user_event_rejected(self):
        user2 = _create_user("bob", "bob@example.com")
        part = HackathonParticipation(
            user=user2,
            event=self.event,
        )
        with self.assertRaises(ValidationError):
            part.save()

    def test_changing_participation_user_rejected(self):
        """Blocker 1: Changing participation user after creation must be rejected."""
        part = _create_participation(self.user, self.event)
        user2 = _create_user("bob", "bob@example.com")

        part.user = user2
        with self.assertRaises(ValidationError) as ctx:
            part.save()
        self.assertIn("user", ctx.exception.message_dict)

        part.refresh_from_db()
        self.assertEqual(part.user, self.user)

    def test_changing_participation_event_rejected(self):
        """Blocker 1: Changing participation event after creation must be rejected."""
        part = _create_participation(self.user, self.event)
        event2 = _create_event(self.user, name="Event 2")

        part.event = event2
        with self.assertRaises(ValidationError) as ctx:
            part.save()
        self.assertIn("event", ctx.exception.message_dict)

        part.refresh_from_db()
        self.assertEqual(part.event, self.event)

    def test_str_representation(self):
        part = _create_participation(self.user, self.event)
        self.assertIn(self.user.username, str(part))
        self.assertIn(self.event.name, str(part))

    def test_cascade_delete_event(self):
        _create_participation(self.user, self.event)
        self.event.delete()
        self.assertEqual(HackathonParticipation.objects.count(), 0)


# ===================================================================
# MODEL TESTS: HackathonAchievement
# ===================================================================


class HackathonAchievementModelTests(APITestCase):

    def setUp(self):
        self.user = _create_user()
        self.event = _create_event(self.user)
        self.participation = _create_participation(
            self.user, self.event, status=HackathonParticipation.Status.ATTENDED
        )

    def test_create_achievement_successfully(self):
        ach = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="1st Place",
            rank=1,
            total_participants=100,
        )
        self.assertEqual(
            ach.verification_status,
            HackathonAchievement.VerificationStatus.SELF_REPORTED,
        )

    def test_multiple_achievements_per_participation(self):
        HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="1st Place",
            rank=1,
        )
        ach2 = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Best AI Project",
        )
        self.assertIsNotNone(ach2.pk)
        self.assertEqual(
            HackathonAchievement.objects.filter(
                participation=self.participation,
            ).count(),
            2,
        )

    def test_custom_award_without_rank(self):
        ach = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="People's Choice Award",
        )
        self.assertIsNone(ach.rank)

    def test_empty_title_rejected_on_save(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="",
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_whitespace_title_rejected_on_save(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="   ",
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_invalid_evidence_url_rejected_on_save(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Valid Award",
            evidence_url="not a valid url",
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_invalid_achievement_type_rejected_on_save(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type="not_a_type",
            title="Award",
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_valid_placement(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="2nd Place",
            rank=2,
            total_participants=50,
        )
        ach.save()
        self.assertIsNotNone(ach.pk)

    def test_rank_zero_rejected_by_model_validation(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Invalid",
            rank=0,
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_rank_zero_rejected_by_database_constraint(self):
        """Blocker 2: Database CheckConstraint must reject rank < 1 even when model validation bypassed."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HackathonAchievement.objects.bulk_create([
                    HackathonAchievement(
                        participation=self.participation,
                        achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
                        title="Rank Zero Direct DB",
                        rank=0,
                    )
                ])

    def test_total_participants_zero_rejected_by_model_validation(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Invalid",
            rank=1,
            total_participants=0,
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_total_participants_zero_rejected_by_database_constraint(self):
        """Blocker 2: Database CheckConstraint must reject total_participants < 1 even when model validation bypassed."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HackathonAchievement.objects.bulk_create([
                    HackathonAchievement(
                        participation=self.participation,
                        achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
                        title="Zero Participants Direct DB",
                        rank=1,
                        total_participants=0,
                    )
                ])

    def test_rank_exceeds_total_participants_rejected_by_model_validation(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Invalid",
            rank=10,
            total_participants=5,
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_rank_exceeds_total_participants_rejected_by_database_constraint(self):
        """Blocker 2: Database CheckConstraint must reject rank > total_participants."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HackathonAchievement.objects.bulk_create([
                    HackathonAchievement(
                        participation=self.participation,
                        achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
                        title="Rank Exceeds Direct DB",
                        rank=10,
                        total_participants=5,
                    )
                ])

    def test_nullable_rank_and_participants_combinations(self):
        # 1. Null rank, null participants
        ach1 = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Award Only",
        )
        self.assertIsNotNone(ach1.pk)

        # 2. Rank present, null participants
        ach2 = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Rank Only",
            rank=3,
        )
        self.assertIsNotNone(ach2.pk)

        # 3. Null rank, participants present
        ach3 = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PARTICIPATION,
            title="Participants Only",
            total_participants=100,
        )
        self.assertIsNotNone(ach3.pk)

        # 4. Rank == total_participants (valid boundary)
        ach4 = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Last Place",
            rank=100,
            total_participants=100,
        )
        self.assertIsNotNone(ach4.pk)

    def test_changing_achievement_participation_rejected(self):
        """Blocker 1: Changing an achievement's participation after creation must be rejected."""
        ach = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Preserved Award",
        )
        event2 = _create_event(self.user, name="Event 2")
        part2 = _create_participation(self.user, event2)

        ach.participation = part2
        with self.assertRaises(ValidationError) as ctx:
            ach.save()
        self.assertIn("participation", ctx.exception.message_dict)

        ach.refresh_from_db()
        self.assertEqual(ach.participation, self.participation)

    def test_mismatched_submission_event_rejected(self):
        event2 = _create_event(self.user, name="Other Event")
        project = _create_project(self.user)
        submission = _create_submission(
            project,
            event2,
            status=HackathonSubmission.Status.SUBMITTED,
        )
        ach = HackathonAchievement(
            participation=self.participation,
            submission=submission,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Wrong Event",
            rank=1,
        )
        with self.assertRaises(ValidationError):
            ach.save()

    def test_matching_submission_accepted(self):
        project = _create_project(self.user)
        submission = _create_submission(
            project,
            self.event,
            status=HackathonSubmission.Status.SUBMITTED,
        )
        ach = HackathonAchievement(
            participation=self.participation,
            submission=submission,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Correct",
            rank=1,
        )
        ach.save()
        self.assertIsNotNone(ach.pk)

    def test_default_verification_is_self_reported(self):
        ach = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PARTICIPATION,
            title="Participated",
        )
        self.assertEqual(
            ach.verification_status,
            HackathonAchievement.VerificationStatus.SELF_REPORTED,
        )

    def test_str_representation(self):
        ach = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Best Demo",
        )
        self.assertIn("Best Demo", str(ach))

    def test_cascade_delete_participation(self):
        HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="1st Place",
            rank=1,
        )
        self.participation.delete()
        self.assertEqual(HackathonAchievement.objects.count(), 0)

    def test_submission_set_null_on_delete(self):
        project = _create_project(self.user)
        submission = _create_submission(
            project,
            self.event,
            status=HackathonSubmission.Status.SUBMITTED,
        )
        ach = HackathonAchievement.objects.create(
            participation=self.participation,
            submission=submission,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="1st Place",
            rank=1,
        )
        submission.delete()
        ach.refresh_from_db()
        self.assertIsNone(ach.submission)
        self.assertEqual(ach.title, "1st Place")


# ===================================================================
# ADMIN TESTS
# ===================================================================


class HackathonAdminReadonlyTests(APITestCase):
    """Test that Django Admin renders immutable parent/relationship fields as readonly."""

    def setUp(self):
        self.site = AdminSite()
        self.user = _create_user()
        self.event = _create_event(self.user)
        self.project = _create_project(self.user)
        self.submission = _create_submission(self.project, self.event)
        self.participation = _create_participation(self.user, self.event)
        self.achievement = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Demo Award",
        )

    def test_event_admin_owner_readonly_on_edit(self):
        ma = HackathonEventAdmin(HackathonEvent, self.site)
        readonly_add = ma.get_readonly_fields(None, obj=None)
        self.assertNotIn("owner", readonly_add)
        readonly_edit = ma.get_readonly_fields(None, obj=self.event)
        self.assertIn("owner", readonly_edit)

    def test_project_admin_owner_readonly_on_edit(self):
        ma = HackathonProjectAdmin(HackathonProject, self.site)
        readonly_edit = ma.get_readonly_fields(None, obj=self.project)
        self.assertIn("owner", readonly_edit)

    def test_submission_admin_relationships_readonly_on_edit(self):
        ma = HackathonSubmissionAdmin(HackathonSubmission, self.site)
        readonly_edit = ma.get_readonly_fields(None, obj=self.submission)
        self.assertIn("project", readonly_edit)
        self.assertIn("event", readonly_edit)

    def test_participation_admin_relationships_readonly_on_edit(self):
        ma = HackathonParticipationAdmin(HackathonParticipation, self.site)
        readonly_edit = ma.get_readonly_fields(None, obj=self.participation)
        self.assertIn("user", readonly_edit)
        self.assertIn("event", readonly_edit)

    def test_achievement_admin_participation_readonly_on_edit(self):
        ma = HackathonAchievementAdmin(HackathonAchievement, self.site)
        readonly_edit = ma.get_readonly_fields(None, obj=self.achievement)
        self.assertIn("participation", readonly_edit)


# ===================================================================
# INDEPENDENCE TESTS
# ===================================================================


class AchievementIndependenceTests(APITestCase):
    """Ensure manually created achievement data is preserved independently
    of connector accounts (PlatformAccount)."""

    def setUp(self):
        self.user = _create_user()
        self.event = _create_event(self.user)
        self.participation = _create_participation(
            self.user,
            self.event,
            status=HackathonParticipation.Status.ATTENDED,
        )
        self.achievement = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Best Innovation",
        )

    def test_achievements_survive_platform_account_deletion(self):
        from apps.connectors.models import PlatformAccount

        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.DEVPOST,
            handle="alice-devpost",
        )
        PlatformAccount.objects.filter(user=self.user).delete()
        self.assertTrue(
            HackathonAchievement.objects.filter(pk=self.achievement.pk).exists()
        )


# ===================================================================
# API TESTS
# ===================================================================


class HackathonOverviewAPITests(APITestCase):

    def setUp(self):
        self.user = _create_user()
        self.other_user = _create_user("bob", "bob@example.com")
        self.url = reverse("hackathon-overview")

    def test_unauthenticated_request_rejected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_overview_returns_zeros(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hackathons_attended"], 0)
        self.assertEqual(response.data["projects_submitted"], 0)
        self.assertEqual(response.data["achievements_recorded"], 0)
        self.assertEqual(response.data["placements_recorded"], 0)

    def test_overview_counts_match_records(self):
        self.client.force_authenticate(self.user)

        event1 = _create_event(self.user, name="Hack A")
        event2 = _create_event(self.user, name="Hack B")

        part1 = _create_participation(
            self.user,
            event1,
            status=HackathonParticipation.Status.ATTENDED,
        )
        part2 = _create_participation(
            self.user,
            event2,
            status=HackathonParticipation.Status.SUBMITTED,
        )

        project = _create_project(self.user)
        _create_submission(
            project,
            event1,
            status=HackathonSubmission.Status.SUBMITTED,
        )

        HackathonAchievement.objects.create(
            participation=part1,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="1st Place",
            rank=1,
        )
        HackathonAchievement.objects.create(
            participation=part2,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Best UI",
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hackathons_attended"], 2)
        self.assertEqual(response.data["projects_submitted"], 1)
        self.assertEqual(response.data["achievements_recorded"], 2)
        self.assertEqual(response.data["placements_recorded"], 1)

    def test_registered_not_counted_as_attended(self):
        self.client.force_authenticate(self.user)

        event = _create_event(self.user)
        _create_participation(
            self.user,
            event,
            status=HackathonParticipation.Status.REGISTERED,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.data["hackathons_attended"], 0)

    def test_draft_submissions_not_counted(self):
        self.client.force_authenticate(self.user)

        event = _create_event(self.user)
        project = _create_project(self.user)
        _create_submission(
            project,
            event,
            status=HackathonSubmission.Status.DRAFT,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.data["projects_submitted"], 0)

    def test_multiple_submissions_one_project_counted_once(self):
        self.client.force_authenticate(self.user)

        event1 = _create_event(self.user, name="Hack A")
        event2 = _create_event(self.user, name="Hack B")
        project = _create_project(self.user)
        _create_submission(
            project,
            event1,
            status=HackathonSubmission.Status.SUBMITTED,
        )
        _create_submission(
            project,
            event2,
            status=HackathonSubmission.Status.SUBMITTED,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.data["projects_submitted"], 1)

    def test_user_cannot_see_other_users_data(self):
        other_event = _create_event(self.other_user, name="Bob's Hack")
        _create_participation(
            self.other_user,
            other_event,
            status=HackathonParticipation.Status.ATTENDED,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data["hackathons_attended"], 0)
        self.assertEqual(response.data["projects_submitted"], 0)
        self.assertEqual(response.data["achievements_recorded"], 0)
        self.assertEqual(response.data["placements_recorded"], 0)

    def test_no_rating_fields_in_response(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        for field in ["rating", "score", "elo", "rating_history", "ranking"]:
            self.assertNotIn(field, response.data)
