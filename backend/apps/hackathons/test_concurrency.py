"""PostgreSQL-only verification/deletion ordering tests.

SQLite ignores SELECT FOR UPDATE, so its test database cannot establish the
row-lock behavior exercised here.
"""

import queue
import threading
import time
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase
from django.test.client import RequestFactory
from rest_framework.test import APIClient

from apps.hackathons.admin import HackathonAchievementAdmin
from apps.hackathons.models import (
    HackathonAchievement, HackathonEvent, HackathonParticipation,
    HackathonProject, HackathonSubmission,
)
from apps.hackathons.views import ManualViewSet


@skipUnless(connection.vendor == "postgresql", "PostgreSQL row locks are required")
class VerifiedDeletionConcurrencyTests(TransactionTestCase):
    databases = {"default"}

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="delete-race-user", email="delete-race@example.com", password="test12345"
        )
        self.admin_user = get_user_model().objects.create_superuser(
            username="delete-race-admin", email="delete-race-admin@example.com", password="test12345"
        )
        self.event = HackathonEvent.objects.create(owner=self.user, name="Race event")
        self.project = HackathonProject.objects.create(owner=self.user, title="Race project")
        self.participation = HackathonParticipation.objects.create(user=self.user, event=self.event)
        self.submission = HackathonSubmission.objects.create(owner=self.user, event=self.event, project=self.project)
        self.achievement = HackathonAchievement.objects.create(
            participation=self.participation, submission=self.submission,
            achievement_type="award", title="Race award",
        )
        self.achievement_admin = HackathonAchievementAdmin(HackathonAchievement, AdminSite())

    def admin_request(self):
        request = RequestFactory().post("/admin/apps/hackathons/hackathonachievement/")
        request.user = self.admin_user
        return request

    def wait_for_row_lock(self, backend_pid, finished):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not finished.is_set():
            with connection.cursor() as cursor:
                cursor.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", [backend_pid])
                row = cursor.fetchone()
            if row and row[0] == "Lock":
                return True
            time.sleep(0.05)
        return False

    def test_admin_verification_wins_over_each_concurrent_user_delete(self):
        targets = (
            ("events", self.event),
            ("projects", self.project),
            ("participations", self.participation),
            ("submissions", self.submission),
            ("achievements", self.achievement),
        )
        for resource, target in targets:
            with self.subTest(resource=resource):
                self.achievement.refresh_from_db()
                self.achievement.verification_status = HackathonAchievement.VerificationStatus.SELF_REPORTED
                self.achievement.save()
                admin_ready = threading.Event()
                release_admin = threading.Event()
                deletion_finished = threading.Event()
                backend_pids = queue.Queue()
                outcomes = []
                failures = []

                def verify_in_admin_transaction():
                    close_old_connections()
                    try:
                        with transaction.atomic():
                            achievement = self.achievement_admin.get_object(self.admin_request(), self.achievement.pk)
                            achievement.verification_status = HackathonAchievement.VerificationStatus.VERIFIED
                            achievement.save()
                            admin_ready.set()
                            if not release_admin.wait(10):
                                raise TimeoutError("Admin transaction was not released")
                    except Exception as exc:
                        failures.append(exc)
                        admin_ready.set()
                    finally:
                        connections.close_all()

                def delete_as_user():
                    close_old_connections()
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT pg_backend_pid()")
                            backend_pids.put(cursor.fetchone()[0])
                        client = APIClient()
                        client.force_authenticate(self.user)
                        outcomes.append(client.delete(f"/api/v1/hackathons/{resource}/{target.pk}/").status_code)
                    except Exception as exc:
                        failures.append(exc)
                    finally:
                        deletion_finished.set()
                        connections.close_all()

                admin_thread = threading.Thread(target=verify_in_admin_transaction)
                delete_thread = threading.Thread(target=delete_as_user)
                admin_thread.start()
                try:
                    self.assertTrue(admin_ready.wait(10), "Admin did not lock the achievement")
                    self.assertFalse(failures, failures)
                    delete_thread.start()
                    backend_pid = backend_pids.get(timeout=10)
                    self.assertTrue(self.wait_for_row_lock(backend_pid, deletion_finished), "User deletion did not wait for the verification row lock")
                finally:
                    release_admin.set()
                    admin_thread.join(timeout=10)
                    if delete_thread.ident is not None:
                        delete_thread.join(timeout=10)

                self.assertFalse(admin_thread.is_alive())
                self.assertFalse(delete_thread.is_alive())
                self.assertFalse(failures, failures)
                self.assertEqual(outcomes, [403])
                self.achievement.refresh_from_db()
                self.assertEqual(self.achievement.verification_status, HackathonAchievement.VerificationStatus.VERIFIED)
                self.assertTrue(type(target).objects.filter(pk=target.pk).exists())

    def test_user_delete_wins_before_admin_verification_reads_current_state(self):
        for resource in ("events", "submissions"):
            with self.subTest(resource=resource):
                event = HackathonEvent.objects.create(owner=self.user, name="Delete first")
                project = HackathonProject.objects.create(owner=self.user, title="Delete first project")
                participation = HackathonParticipation.objects.create(user=self.user, event=event)
                submission = HackathonSubmission.objects.create(owner=self.user, event=event, project=project)
                achievement = HackathonAchievement.objects.create(
                    participation=participation, submission=submission,
                    achievement_type="award", title="Delete first award",
                )
                target = event if resource == "events" else submission
                deletion_locked = threading.Event()
                release_delete = threading.Event()
                admin_finished = threading.Event()
                backend_pids = queue.Queue()
                delete_statuses = []
                admin_results = []
                failures = []
                original_destroy = ManualViewSet.perform_destroy

                def paused_destroy(view, instance):
                    if isinstance(instance, type(target)) and instance.pk == target.pk:
                        deletion_locked.set()
                        if not release_delete.wait(10):
                            raise TimeoutError("Deletion transaction was not released")
                    return original_destroy(view, instance)

                def delete_as_user():
                    close_old_connections()
                    try:
                        client = APIClient()
                        client.force_authenticate(self.user)
                        delete_statuses.append(client.delete(f"/api/v1/hackathons/{resource}/{target.pk}/").status_code)
                    except Exception as exc:
                        failures.append(exc)
                        deletion_locked.set()
                    finally:
                        connections.close_all()

                def verify_as_admin():
                    close_old_connections()
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT pg_backend_pid()")
                            backend_pids.put(cursor.fetchone()[0])
                        with transaction.atomic():
                            current = self.achievement_admin.get_object(self.admin_request(), achievement.pk)
                            if current is None:
                                admin_results.append(("missing", None))
                            else:
                                admin_results.append(("seen", current.submission_id))
                                current.verification_status = HackathonAchievement.VerificationStatus.VERIFIED
                                current.save()
                    except Exception as exc:
                        failures.append(exc)
                    finally:
                        admin_finished.set()
                        connections.close_all()

                delete_thread = threading.Thread(target=delete_as_user)
                admin_thread = threading.Thread(target=verify_as_admin)
                with patch.object(ManualViewSet, "perform_destroy", paused_destroy):
                    delete_thread.start()
                    try:
                        self.assertTrue(deletion_locked.wait(10), "Deletion did not reach the locked section")
                        self.assertFalse(failures, failures)
                        admin_thread.start()
                        backend_pid = backend_pids.get(timeout=10)
                        self.assertTrue(self.wait_for_row_lock(backend_pid, admin_finished), "Admin verification did not wait for the delete lock")
                    finally:
                        release_delete.set()
                        delete_thread.join(timeout=10)
                        if admin_thread.ident is not None:
                            admin_thread.join(timeout=10)

                self.assertFalse(delete_thread.is_alive())
                self.assertFalse(admin_thread.is_alive())
                self.assertFalse(failures, failures)
                self.assertEqual(delete_statuses, [204])
                if resource == "events":
                    self.assertEqual(admin_results, [("missing", None)])
                    self.assertFalse(HackathonAchievement.objects.filter(pk=achievement.pk).exists())
                else:
                    self.assertEqual(admin_results, [("seen", None)])
                    achievement.refresh_from_db()
                    self.assertIsNone(achievement.submission_id)
                    self.assertEqual(achievement.verification_status, HackathonAchievement.VerificationStatus.VERIFIED)
