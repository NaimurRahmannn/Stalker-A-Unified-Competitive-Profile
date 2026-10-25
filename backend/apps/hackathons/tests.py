"""Tests for the hackathons app — Phase 1.

Covers model creation, validation, constraints, ownership checks, deletion
behavior, and the overview API endpoint.
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

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
# MODEL TESTS
# ===================================================================


class HackathonEventModelTests(APITestCase):
    """Tests for HackathonEvent creation, validation, and constraints."""

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

    def test_end_date_before_start_date_rejected(self):
        event = HackathonEvent(
            owner=self.user,
            name="Bad Dates",
            start_date=datetime.date(2025, 6, 15),
            end_date=datetime.date(2025, 6, 10),
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

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

    def test_duplicate_external_id_same_source_rejected(self):
        _create_event(
            self.user, source=HackathonEvent.Source.DEVPOST,
            external_id="devpost-123",
        )
        with self.assertRaises(IntegrityError):
            _create_event(
                self.user, source=HackathonEvent.Source.DEVPOST,
                external_id="devpost-123",
            )

    def test_empty_external_id_duplicates_allowed(self):
        _create_event(self.user, external_id="")
        event2 = _create_event(self.user, external_id="")
        self.assertIsNotNone(event2.pk)

    def test_same_external_id_different_users_allowed(self):
        user2 = _create_user("bob", "bob@example.com")
        _create_event(
            self.user, source=HackathonEvent.Source.DEVPOST,
            external_id="devpost-123",
        )
        event2 = _create_event(
            user2, source=HackathonEvent.Source.DEVPOST,
            external_id="devpost-123",
        )
        self.assertIsNotNone(event2.pk)

    def test_cascade_delete_with_owner(self):
        _create_event(self.user)
        self.user.delete()
        self.assertEqual(HackathonEvent.objects.count(), 0)


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

    def test_technologies_must_be_list_of_strings(self):
        project = HackathonProject(
            owner=self.user,
            title="Bad Tech",
            technologies={"key": "value"},
        )
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_technologies_non_string_elements_rejected(self):
        project = HackathonProject(
            owner=self.user,
            title="Bad Tech",
            technologies=["Python", 42],
        )
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_duplicate_external_id_rejected(self):
        _create_project(
            self.user, source=HackathonProject.Source.DEVPOST,
            external_id="dp-proj-1",
        )
        with self.assertRaises(IntegrityError):
            _create_project(
                self.user, source=HackathonProject.Source.DEVPOST,
                external_id="dp-proj-1",
            )

    def test_empty_external_id_duplicates_allowed(self):
        _create_project(self.user, external_id="")
        p2 = _create_project(self.user, title="Another", external_id="")
        self.assertIsNotNone(p2.pk)

    def test_cascade_delete_with_owner(self):
        _create_project(self.user)
        self.user.delete()
        self.assertEqual(HackathonProject.objects.count(), 0)


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
        with self.assertRaises(IntegrityError):
            _create_submission(self.project, self.event)

    def test_cross_user_submission_rejected(self):
        user2 = _create_user("bob", "bob@example.com")
        other_event = _create_event(user2, name="Bob's Event")
        sub = HackathonSubmission(
            project=self.project, event=other_event,
        )
        with self.assertRaises(ValidationError):
            sub.full_clean()

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


class HackathonParticipationModelTests(APITestCase):

    def setUp(self):
        self.user = _create_user()
        self.event = _create_event(self.user)

    def test_create_participation_successfully(self):
        part = _create_participation(self.user, self.event)
        self.assertEqual(part.status, HackathonParticipation.Status.REGISTERED)
        self.assertEqual(part.user, self.user)

    def test_participation_without_project(self):
        """A participation record does not require a project."""
        part = _create_participation(self.user, self.event)
        self.assertIsNotNone(part.pk)
        self.assertEqual(HackathonProject.objects.count(), 0)

    def test_duplicate_participation_rejected(self):
        _create_participation(self.user, self.event)
        with self.assertRaises(IntegrityError):
            _create_participation(self.user, self.event)

    def test_cross_user_event_rejected(self):
        user2 = _create_user("bob", "bob@example.com")
        part = HackathonParticipation(
            user=user2, event=self.event,
        )
        with self.assertRaises(ValidationError):
            part.full_clean()

    def test_str_representation(self):
        part = _create_participation(self.user, self.event)
        self.assertIn(self.user.username, str(part))
        self.assertIn(self.event.name, str(part))

    def test_cascade_delete_event(self):
        _create_participation(self.user, self.event)
        self.event.delete()
        self.assertEqual(HackathonParticipation.objects.count(), 0)


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

    def test_valid_placement(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="2nd Place",
            rank=2,
            total_participants=50,
        )
        ach.full_clean()  # Should not raise

    def test_rank_zero_rejected(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Invalid",
            rank=0,
        )
        with self.assertRaises(ValidationError):
            ach.full_clean()

    def test_total_participants_zero_rejected(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Invalid",
            rank=1,
            total_participants=0,
        )
        with self.assertRaises(ValidationError):
            ach.full_clean()

    def test_rank_exceeds_total_participants_rejected(self):
        ach = HackathonAchievement(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Invalid",
            rank=10,
            total_participants=5,
        )
        with self.assertRaises(ValidationError):
            ach.full_clean()

    def test_mismatched_submission_event_rejected(self):
        """Achievement submission must belong to the same event as
        participation."""
        event2 = _create_event(self.user, name="Other Event")
        project = _create_project(self.user)
        submission = _create_submission(
            project, event2,
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
            ach.full_clean()

    def test_matching_submission_accepted(self):
        project = _create_project(self.user)
        submission = _create_submission(
            project, self.event,
            status=HackathonSubmission.Status.SUBMITTED,
        )
        ach = HackathonAchievement(
            participation=self.participation,
            submission=submission,
            achievement_type=HackathonAchievement.AchievementType.PLACEMENT,
            title="Correct",
            rank=1,
        )
        ach.full_clean()  # Should not raise

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
            project, self.event,
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


class DuplicateExternalIdConstraintTests(APITestCase):
    """Verify that external identity uniqueness prevents imported duplicates."""

    def setUp(self):
        self.user = _create_user()

    def test_event_duplicate_imported_external_id(self):
        _create_event(
            self.user, source=HackathonEvent.Source.DEVPOST,
            external_id="ext-ev-1",
        )
        with self.assertRaises(IntegrityError):
            _create_event(
                self.user, source=HackathonEvent.Source.DEVPOST,
                external_id="ext-ev-1",
            )

    def test_project_duplicate_imported_external_id(self):
        _create_project(
            self.user, source=HackathonProject.Source.DEVPOST,
            external_id="ext-proj-1",
        )
        with self.assertRaises(IntegrityError):
            _create_project(
                self.user, title="Another",
                source=HackathonProject.Source.DEVPOST,
                external_id="ext-proj-1",
            )


class AchievementIndependenceTests(APITestCase):
    """Ensure manually created achievement data is preserved independently
    of connector accounts (PlatformAccount)."""

    def setUp(self):
        self.user = _create_user()
        self.event = _create_event(self.user)
        self.participation = _create_participation(
            self.user, self.event,
            status=HackathonParticipation.Status.ATTENDED,
        )
        self.achievement = HackathonAchievement.objects.create(
            participation=self.participation,
            achievement_type=HackathonAchievement.AchievementType.AWARD,
            title="Best Innovation",
        )

    def test_achievements_survive_platform_account_deletion(self):
        """Deleting a PlatformAccount must not cascade to hackathon
        achievements — there is no FK between them."""
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

    # ------------------------------------------------------------------
    # 1. Unauthenticated request is rejected
    # ------------------------------------------------------------------
    def test_unauthenticated_request_rejected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # 2. Authenticated empty overview returns zeros
    # ------------------------------------------------------------------
    def test_empty_overview_returns_zeros(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["hackathons_attended"], 0)
        self.assertEqual(response.data["projects_submitted"], 0)
        self.assertEqual(response.data["achievements_recorded"], 0)
        self.assertEqual(response.data["placements_recorded"], 0)

    # ------------------------------------------------------------------
    # 3. Overview counts match stored test records
    # ------------------------------------------------------------------
    def test_overview_counts_match_records(self):
        self.client.force_authenticate(self.user)

        event1 = _create_event(self.user, name="Hack A")
        event2 = _create_event(self.user, name="Hack B")

        part1 = _create_participation(
            self.user, event1,
            status=HackathonParticipation.Status.ATTENDED,
        )
        part2 = _create_participation(
            self.user, event2,
            status=HackathonParticipation.Status.SUBMITTED,
        )

        project = _create_project(self.user)
        _create_submission(
            project, event1,
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

    # ------------------------------------------------------------------
    # 4. Registered-only events are not counted as attended
    # ------------------------------------------------------------------
    def test_registered_not_counted_as_attended(self):
        self.client.force_authenticate(self.user)

        event = _create_event(self.user)
        _create_participation(
            self.user, event,
            status=HackathonParticipation.Status.REGISTERED,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.data["hackathons_attended"], 0)

    # ------------------------------------------------------------------
    # 5. Draft submissions are not counted as submitted projects
    # ------------------------------------------------------------------
    def test_draft_submissions_not_counted(self):
        self.client.force_authenticate(self.user)

        event = _create_event(self.user)
        project = _create_project(self.user)
        _create_submission(
            project, event,
            status=HackathonSubmission.Status.DRAFT,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.data["projects_submitted"], 0)

    # ------------------------------------------------------------------
    # 6. Multiple submissions of one project count as one distinct project
    # ------------------------------------------------------------------
    def test_multiple_submissions_one_project_counted_once(self):
        self.client.force_authenticate(self.user)

        event1 = _create_event(self.user, name="Hack A")
        event2 = _create_event(self.user, name="Hack B")
        project = _create_project(self.user)
        _create_submission(
            project, event1,
            status=HackathonSubmission.Status.SUBMITTED,
        )
        _create_submission(
            project, event2,
            status=HackathonSubmission.Status.SUBMITTED,
        )

        response = self.client.get(self.url)
        self.assertEqual(response.data["projects_submitted"], 1)

    # ------------------------------------------------------------------
    # 7. Authenticated user cannot see another user's statistics
    # ------------------------------------------------------------------
    def test_user_cannot_see_other_users_data(self):
        # Create data for other_user
        other_event = _create_event(self.other_user, name="Bob's Hack")
        _create_participation(
            self.other_user, other_event,
            status=HackathonParticipation.Status.ATTENDED,
        )

        # Authenticate as self.user
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data["hackathons_attended"], 0)
        self.assertEqual(response.data["projects_submitted"], 0)
        self.assertEqual(response.data["achievements_recorded"], 0)
        self.assertEqual(response.data["placements_recorded"], 0)

    # ------------------------------------------------------------------
    # 8. No rating fields in overview response
    # ------------------------------------------------------------------
    def test_no_rating_fields_in_response(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        for field in ["rating", "score", "elo", "rating_history", "ranking"]:
            self.assertNotIn(field, response.data)
