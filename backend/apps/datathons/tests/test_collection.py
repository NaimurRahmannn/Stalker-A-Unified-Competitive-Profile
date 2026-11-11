from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.connectors.models import PlatformAccount
from apps.datathons.linking import link_kaggle_account
from apps.datathons.models import KaggleCollectionRun, KaggleProfile, KaggleTrackStats
from apps.datathons.services.collection import collect_kaggle_profile
from apps.datathons.services.providers import (
    CollectionError, PROVIDERS, ProviderPolicy, ProviderRegistration, ProviderUnavailable,
)
from apps.datathons.services.queue import CooldownActive, dispatch_kaggle_run, request_kaggle_collection
from apps.datathons.services.scheduling import (
    cleanup_old_runs, dispatch_pending_runs, recover_stale_runs, schedule_due_profiles,
)
from apps.datathons.tasks import process_collection_run


User = get_user_model()
FIXTURE = Path(__file__).resolve().parents[2] / "connectors/providers/kaggle/tests/fixtures/complete_profile.html"
POLICY = ProviderPolicy(max_concurrency=2, min_interval_seconds=0, max_attempts=3,
                        request_timeout_seconds=10, max_response_bytes=1_000_000)


class SyntheticProvider:
    def load(self, expected_username):
        return FIXTURE.read_text(encoding="utf-8")


def profile(username="example_user"):
    return KaggleProfile.objects.create(
        username=username, normalized_username=username.casefold(),
        profile_url=f"https://www.kaggle.com/{username}",
    )


def run_for(item, **kwargs):
    row = KaggleCollectionRun(profile=item, trigger="manual", provider_name="mock", **kwargs)
    if row.task_id is None:
        row.task_id = str(row.pk)
    row.save()
    return row


@override_settings(KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="mock")
class CollectionTests(TestCase):
    def setUp(self):
        self.registration = patch.dict(PROVIDERS, {"mock": ProviderRegistration(SyntheticProvider, POLICY)})
        self.registration.start()
        self.addCleanup(self.registration.stop)
        self.profile = profile()
        owner = User.objects.create_user(username="collection_owner", email="collection_owner@example.com")
        link_kaggle_account(PlatformAccount.objects.create(
            user=owner, platform="kaggle", handle=self.profile.username,
        ))

    def test_active_run_is_unique_and_fields_are_constrained(self):
        first = run_for(self.profile)
        self.assertEqual(first.status, "queued")
        for changes in ({"trigger": "invalid"}, {"status": "unknown"},
                        {"attempt_count": 4, "max_attempts": 3}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                KaggleCollectionRun.objects.filter(pk=first.pk).update(**changes)
        with self.assertRaises(IntegrityError), transaction.atomic():
            run_for(self.profile)
        second_profile = profile("other_user")
        with self.assertRaises(IntegrityError), transaction.atomic():
            run_for(second_profile, task_id=first.task_id)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_queue_deduplicates_and_enforces_cooldown(self, publish):
        with self.captureOnCommitCallbacks(execute=True):
            first = request_kaggle_collection(self.profile)
        self.assertFalse(first.deduplicated)
        publish.assert_called_once()
        second = request_kaggle_collection(self.profile)
        self.assertTrue(second.deduplicated)
        self.assertEqual(first.run.pk, second.run.pk)
        KaggleCollectionRun.objects.filter(pk=first.run.pk).update(status="succeeded", finished_at=timezone.now())
        with self.assertRaises(CooldownActive):
            request_kaggle_collection(self.profile)

    def test_disabled_provider_creates_no_run(self):
        with override_settings(KAGGLE_COLLECTION_ENABLED=False):
            with self.assertRaises(CollectionError) as raised:
                request_kaggle_collection(self.profile)
        self.assertEqual(raised.exception.code, "provider_disabled")
        with override_settings(KAGGLE_PROVIDER_NAME="unregistered"):
            with self.assertRaises(CollectionError) as raised:
                request_kaggle_collection(self.profile)
        self.assertEqual(raised.exception.code, "provider_disabled")
        self.assertFalse(KaggleCollectionRun.objects.exists())

    def test_synthetic_collection_uses_existing_persistence(self):
        result = collect_kaggle_profile(self.profile, provider=SyntheticProvider(), policy=POLICY)
        self.assertEqual(result.track_count, 3)
        self.assertEqual(KaggleTrackStats.objects.get(profile=self.profile, track="competitions").global_rank, 1234)

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_task_success_and_duplicate_delivery(self, slot):
        run = run_for(self.profile, last_dispatch_error_code="broker_unavailable")
        self.assertEqual(process_collection_run(run.pk), "succeeded")
        self.assertEqual(process_collection_run(run.pk), "terminal")
        run.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(run.attempt_count, 1)
        self.assertEqual(run.last_dispatch_error_code, "")
        self.assertEqual(self.profile.collection_status, "success")
        self.assertGreater(self.profile.next_refresh_at, timezone.now())
        self.assertEqual(KaggleTrackStats.objects.filter(profile=self.profile).count(), 3)

    def test_task_respects_active_lease(self):
        run = run_for(self.profile, status="running", attempt_count=1,
                      lease_expires_at=timezone.now() + timedelta(minutes=2))
        with patch.object(SyntheticProvider, "load", side_effect=AssertionError("provider was called")):
            self.assertEqual(process_collection_run(run.pk), "leased")
        run.refresh_from_db()
        self.assertEqual(run.attempt_count, 1)

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_unexpected_provider_error_is_not_retried(self, slot):
        run = run_for(self.profile)
        with patch.object(SyntheticProvider, "load", side_effect=RuntimeError("programming error")):
            with self.assertRaises(RuntimeError):
                process_collection_run(run.pk)
        run.refresh_from_db()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.error_code, "internal_error")

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_bad_document_is_terminal_and_preserves_cached_data(self, slot):
        collect_kaggle_profile(self.profile, provider=SyntheticProvider(), policy=POLICY)
        self.profile.refresh_from_db()
        previous_success = self.profile.last_successful_at
        run = run_for(self.profile)
        with patch.object(SyntheticProvider, "load", return_value="<html>bad</html>"):
            self.assertEqual(process_collection_run(run.pk), "failed")
        run.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(run.error_code, "unsupported_markup")
        self.assertEqual(self.profile.last_successful_at, previous_success)
        self.assertEqual(KaggleTrackStats.objects.get(profile=self.profile, track="competitions").global_rank, 1234)

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_identity_mismatch_is_terminal(self, slot):
        run = run_for(self.profile)
        wrong_document = FIXTURE.read_text(encoding="utf-8").replace('"username":"example_user"',
                                                                      '"username":"other_user"')
        with patch.object(SyntheticProvider, "load", return_value=wrong_document):
            self.assertEqual(process_collection_run(run.pk), "failed")
        run.refresh_from_db()
        self.assertEqual(run.attempt_count, 1)
        self.assertEqual(run.error_code, "identity_mismatch")

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_transient_retry_and_exhaustion(self, publish, slot):
        run = run_for(self.profile, max_attempts=2)
        with patch.object(SyntheticProvider, "load", side_effect=ProviderUnavailable()):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(process_collection_run(run.pk), "retrying")
            run.refresh_from_db()
            self.assertEqual(run.attempt_count, 1)
            self.assertGreater(run.next_attempt_at, timezone.now())
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.collection_status, "not_collected")
            self.assertEqual(process_collection_run(run.pk), "waiting")
            KaggleCollectionRun.objects.filter(pk=run.pk).update(next_attempt_at=timezone.now() - timedelta(seconds=1))
            self.assertEqual(process_collection_run(run.pk), "failed")
        run.refresh_from_db()
        self.assertEqual(run.attempt_count, 2)
        self.assertEqual(run.error_code, "provider_unavailable")
        self.assertIsNone(run.lease_expires_at)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async", side_effect=ConnectionError("broker down"))
    def test_broker_failure_is_recorded_without_mutating_profile(self, publish):
        with self.captureOnCommitCallbacks(execute=True):
            result = request_kaggle_collection(self.profile)
        result.run.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(result.run.status, "queued")
        self.assertEqual(result.run.last_dispatch_error_code, "broker_unavailable")
        self.assertEqual(self.profile.collection_status, "not_collected")
        self.assertIsNotNone(result.run.next_dispatch_at)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_dispatch_pending_recovers_broker_failure(self, publish):
        run = run_for(self.profile, next_dispatch_at=timezone.now() - timedelta(seconds=1),
                      last_dispatch_error_code="broker_unavailable")
        self.assertEqual(dispatch_pending_runs(), 1)
        run.refresh_from_db()
        self.assertEqual(run.last_dispatch_error_code, "")
        self.assertIsNotNone(run.dispatched_at)
        self.assertEqual(dispatch_pending_runs(), 0)

    def test_bounded_dispatch_does_not_publish_forever(self):
        run = run_for(self.profile, dispatch_attempts=5, next_dispatch_at=timezone.now() - timedelta(seconds=1))
        with patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async") as publish:
            self.assertFalse(dispatch_kaggle_run(run.pk))
            publish.assert_not_called()
        run.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.error_code, "dispatch_exhausted")
        self.assertGreater(self.profile.next_refresh_at, timezone.now())

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_recovery_respects_lease_and_attempt_limit(self, publish):
        run = run_for(self.profile, status="running", attempt_count=1,
                      lease_expires_at=timezone.now() + timedelta(minutes=5))
        self.assertEqual(recover_stale_runs(), 0)
        KaggleCollectionRun.objects.filter(pk=run.pk).update(lease_expires_at=timezone.now() - timedelta(seconds=1))
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(recover_stale_runs(), 1)
        run.refresh_from_db()
        self.assertEqual(run.status, "retrying")
        self.assertEqual(run.error_code, "worker_lost")
        KaggleCollectionRun.objects.filter(pk=run.pk).update(
            status="running", attempt_count=run.max_attempts,
            lease_expires_at=timezone.now() - timedelta(seconds=1),
        )
        self.assertEqual(recover_stale_runs(), 1)
        run.refresh_from_db()
        self.assertEqual(run.status, "failed")
        self.assertEqual(recover_stale_runs(), 0)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_scheduler_is_bounded_and_skips_unlinked_future_and_active(self, publish):
        user = User.objects.create_user(username="scheduler", email="scheduler@example.com", password="password123")
        due = [self.profile, profile("second_user"), profile("third_user")]
        link_kaggle_account(PlatformAccount.objects.create(user=user, platform="kaggle", handle=due[0].username))
        # A second owner shares the first profile and must not create another job.
        other = User.objects.create_user(username="other", email="other@example.com", password="password123")
        link_kaggle_account(PlatformAccount.objects.create(user=other, platform="kaggle", handle=due[0].username))
        second_owner = User.objects.create_user(username="second", email="second@example.com", password="password123")
        link_kaggle_account(PlatformAccount.objects.create(
            user=second_owner, platform="kaggle", handle=due[1].username,
        ))
        future = profile("future_user")
        future.next_refresh_at = timezone.now() + timedelta(days=1)
        future.save(update_fields=["next_refresh_at"])
        link_kaggle_account(PlatformAccount.objects.create(
            user=User.objects.create_user(username="future", email="future@example.com", password="password123"),
            platform="kaggle", handle=future.username,
        ))
        with override_settings(KAGGLE_SCHEDULED_SYNC_ENABLED=False):
            self.assertEqual(schedule_due_profiles(), 0)
        with override_settings(KAGGLE_SCHEDULED_SYNC_ENABLED=True, KAGGLE_SCHEDULER_BATCH_SIZE=1):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(schedule_due_profiles(), 1)
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(schedule_due_profiles(), 1)
            self.assertEqual(schedule_due_profiles(), 0)
        self.assertEqual(KaggleCollectionRun.objects.count(), 2)

    def test_cleanup_deletes_only_old_terminal_runs(self):
        old = run_for(self.profile, status="succeeded", finished_at=timezone.now() - timedelta(days=60))
        live = run_for(self.profile, status="queued")
        self.assertEqual(cleanup_old_runs(), 1)
        self.assertFalse(KaggleCollectionRun.objects.filter(pk=old.pk).exists())
        self.assertTrue(KaggleCollectionRun.objects.filter(pk=live.pk).exists())
        self.assertTrue(KaggleProfile.objects.filter(pk=self.profile.pk).exists())


@override_settings(KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="mock")
class CollectionAPITests(APITestCase):
    def setUp(self):
        self.registration = patch.dict(PROVIDERS, {"mock": ProviderRegistration(SyntheticProvider, POLICY)})
        self.registration.start()
        self.addCleanup(self.registration.stop)
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="password123")
        self.other = User.objects.create_user(username="bob", email="bob@example.com", password="password123")
        self.sync_url = reverse("kaggle-sync")
        self.status_url = reverse("kaggle-sync-status")

    def test_auth_missing_link_and_disabled_provider(self):
        self.assertEqual(self.client.post(self.sync_url).status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.sync_url).status_code, 404)
        account = PlatformAccount.objects.create(user=self.user, platform="kaggle", handle="example_user")
        link_kaggle_account(account)
        with override_settings(KAGGLE_COLLECTION_ENABLED=False):
            response = self.client.post(self.sync_url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["code"], "provider_disabled")
        self.assertEqual(KaggleCollectionRun.objects.count(), 0)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_queue_status_deduplication_and_cross_user_isolation(self, publish):
        account = PlatformAccount.objects.create(user=self.user, platform="kaggle", handle="example_user")
        linked = link_kaggle_account(account)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.status_url).data["status"], "not_started")
        self.assertEqual(self.client.post(self.sync_url, {"username": "other_user"}).status_code, 400)
        with self.captureOnCommitCallbacks(execute=True):
            first = self.client.post(self.sync_url)
        self.assertEqual(first.status_code, 202, first.data)
        self.assertFalse(first.data["deduplicated"])
        second = self.client.post(self.sync_url)
        self.assertEqual(second.status_code, 202)
        self.assertTrue(second.data["deduplicated"])
        self.assertEqual(first.data["run_id"], second.data["run_id"])
        self.assertEqual(self.client.get(self.status_url).data["status"], "queued")
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.status_url).status_code, 404)
        other_account = PlatformAccount.objects.create(user=self.other, platform="kaggle", handle="example_user")
        link_kaggle_account(other_account)
        shared = self.client.get(self.status_url)
        self.assertEqual(shared.status_code, 200)
        self.assertEqual(shared.data["run_id"], first.data["run_id"])
        self.assertNotIn("requested_by", shared.data)
        PlatformAccount.objects.filter(pk=other_account.pk).update(handle="different_user")
        self.assertEqual(self.client.get(self.status_url).status_code, 409)
        self.assertEqual(self.client.post(self.sync_url).status_code, 409)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_manual_cooldown_returns_retry_after(self, publish):
        account = PlatformAccount.objects.create(user=self.user, platform="kaggle", handle="example_user")
        link_kaggle_account(account)
        self.client.force_authenticate(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            first = self.client.post(self.sync_url)
        KaggleCollectionRun.objects.filter(pk=first.data["run_id"]).update(
            status="succeeded", finished_at=timezone.now(),
        )
        response = self.client.post(self.sync_url)
        self.assertEqual(response.status_code, 429)
        self.assertGreater(response.data["retry_after_seconds"], 0)


@override_settings(KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="mock")
class CollectionPostgresConcurrencyTests(TransactionTestCase):
    def test_simultaneous_requests_share_active_run(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locking required")
        item = profile()
        owner = User.objects.create_user(username="concurrent_owner", email="concurrent_owner@example.com")
        link_kaggle_account(PlatformAccount.objects.create(user=owner, platform="kaggle", handle=item.username))
        barrier = Barrier(2)
        with patch.dict(PROVIDERS, {"mock": ProviderRegistration(SyntheticProvider, POLICY)}), patch(
            "apps.datathons.tasks.collect_kaggle_profile_task.apply_async"
        ):
            def request_one():
                close_old_connections()
                try:
                    barrier.wait(timeout=10)
                    return request_kaggle_collection(item).run.pk
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as pool:
                ids = list(pool.map(lambda _: request_one(), range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(KaggleCollectionRun.objects.filter(profile=item).count(), 1)
