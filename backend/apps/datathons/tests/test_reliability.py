from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import nullcontext
from datetime import timedelta
from threading import Barrier, Event
from unittest.mock import patch
from uuid import uuid4

from celery.contrib.testing.worker import start_worker
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from redis import RedisError

from apps.connectors.models import PlatformAccount
from apps.connectors.serializers import PlatformAccountSerializer
from apps.connectors.views import PlatformAccountViewSet
from apps.datathons.linking import link_kaggle_account
from apps.datathons.models import KaggleCollectionRun, KaggleProfile, KaggleTrackStats
from apps.datathons.services.providers import (
    CollectionError, PROVIDERS, ProviderPolicy, ProviderRegistration, ProviderUnavailable,
)
from apps.datathons.services.queue import request_kaggle_collection
from apps.datathons.services.scheduling import dispatch_pending_runs, schedule_due_profiles
from apps.datathons.services.throttle import _ACQUIRE, _RELEASE, _redis_client, provider_slot
from apps.datathons.tasks import process_collection_run
from apps.datathons.tasks import collect_kaggle_profile_task
from config.celery import app as celery_app

from .redis_worker import acquire_in_process
from .test_collection import POLICY, SyntheticProvider, profile, run_for


User = get_user_model()


@override_settings(KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="mock")
class SchedulingReliabilityTests(TestCase):
    def setUp(self):
        self.registration = patch.dict(PROVIDERS, {"mock": ProviderRegistration(SyntheticProvider, POLICY)})
        self.registration.start()
        self.addCleanup(self.registration.stop)
        self.serial = 0

    def linked(self, name):
        self.serial += 1
        item = profile(name)
        owner = User.objects.create_user(
            username=f"owner{self.serial}", email=f"owner{self.serial}@example.com",
        )
        account = PlatformAccount.objects.create(user=owner, platform="kaggle", handle=name)
        link_kaggle_account(account)
        return item, account

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_invalid_profiles_are_deferred_without_starving_valid_profiles(self, publish):
        first, _ = self.linked("first_bad")
        second, _ = self.linked("second_bad")
        good, _ = self.linked("good_profile")
        KaggleProfile.objects.filter(pk__in=[first.pk, second.pk]).update(username="invalid!")
        with override_settings(KAGGLE_SCHEDULED_SYNC_ENABLED=True, KAGGLE_SCHEDULER_BATCH_SIZE=3):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(schedule_due_profiles(), 1)
            self.assertEqual(schedule_due_profiles(), 0)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.last_error_code, "invalid_identity")
        self.assertEqual(second.last_error_code, "invalid_identity")
        self.assertGreater(first.next_refresh_at, timezone.now())
        self.assertGreater(second.next_refresh_at, timezone.now())
        self.assertEqual(KaggleCollectionRun.objects.get().profile_id, good.pk)
        self.assertEqual(publish.call_count, 1)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_batch_limit_and_deterministic_order_survive_bad_profile(self, publish):
        bad, _ = self.linked("bad_first")
        good, _ = self.linked("good_second")
        later, _ = self.linked("good_third")
        KaggleProfile.objects.filter(pk=bad.pk).update(username="invalid!")
        with override_settings(KAGGLE_SCHEDULED_SYNC_ENABLED=True, KAGGLE_SCHEDULER_BATCH_SIZE=2):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(schedule_due_profiles(), 1)
            self.assertEqual(list(KaggleCollectionRun.objects.values_list("profile_id", flat=True)), [good.pk])
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(schedule_due_profiles(), 1)
        self.assertEqual(set(KaggleCollectionRun.objects.values_list("profile_id", flat=True)), {good.pk, later.pk})

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_all_invalid_profiles_defer_and_keep_cached_data(self, publish):
        first, _ = self.linked("bad_a")
        second, _ = self.linked("bad_b")
        KaggleProfile.objects.filter(pk__in=[first.pk, second.pk]).update(username="invalid!")
        with override_settings(KAGGLE_SCHEDULED_SYNC_ENABLED=True, KAGGLE_SCHEDULER_BATCH_SIZE=2):
            self.assertEqual(schedule_due_profiles(), 0)
            self.assertEqual(schedule_due_profiles(), 0)
        self.assertFalse(KaggleCollectionRun.objects.exists())
        publish.assert_not_called()
        self.assertEqual(KaggleTrackStats.objects.count(), 0)

    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_benchmark_scheduler_scope_excludes_other_profiles(self, publish):
        genuine, _ = self.linked("genuine_profile")
        synthetic, _ = self.linked("kbench_scope_one")
        with override_settings(KAGGLE_SCHEDULED_SYNC_ENABLED=True):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(schedule_due_profiles(profile_prefix="kbench_scope_"), 1)
        self.assertEqual(list(KaggleCollectionRun.objects.values_list("profile_id", flat=True)), [synthetic.pk])
        self.assertIsNone(KaggleProfile.objects.get(pk=genuine.pk).next_refresh_at)


@override_settings(KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="mock")
class CollectionLifecycleReliabilityTests(TestCase):
    def setUp(self):
        self.registration = patch.dict(PROVIDERS, {"mock": ProviderRegistration(SyntheticProvider, POLICY)})
        self.registration.start()
        self.addCleanup(self.registration.stop)
        self.item = profile()
        self.owner = User.objects.create_user(username="owner", email="owner@example.com")
        self.account = PlatformAccount.objects.create(user=self.owner, platform="kaggle", handle=self.item.username)
        link_kaggle_account(self.account)

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_last_unlink_cancels_before_provider_and_duplicate_is_terminal(self, slot):
        run = run_for(self.item)
        self.account.delete()
        with self.assertRaises(CollectionError) as unavailable:
            request_kaggle_collection(self.item)
        self.assertEqual(unavailable.exception.code, "no_valid_link")
        with patch.object(SyntheticProvider, "load", side_effect=AssertionError("provider called")) as load:
            self.assertEqual(process_collection_run(run.pk), "cancelled")
            self.assertEqual(process_collection_run(run.pk), "terminal")
            load.assert_not_called()
        run.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(run.status, "cancelled")
        self.assertEqual(run.error_code, "no_valid_link")
        self.assertEqual(self.item.collection_status, "not_collected")
        self.assertIsNone(self.item.next_refresh_at)

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_shared_profile_continues_after_one_owner_unlinks(self, slot):
        other = User.objects.create_user(username="other", email="other@example.com")
        link_kaggle_account(PlatformAccount.objects.create(
            user=other, platform="kaggle", handle=self.item.username,
        ))
        run = run_for(self.item)
        self.account.delete()
        self.assertEqual(process_collection_run(run.pk), "succeeded")
        self.assertTrue(KaggleTrackStats.objects.filter(profile=self.item).exists())

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_stale_account_identity_and_waiting_retry_cancel(self, slot):
        run = run_for(self.item, status="retrying", attempt_count=1,
                      next_attempt_at=timezone.now() + timedelta(hours=1))
        PlatformAccount.objects.filter(pk=self.account.pk).update(handle="different_user")
        self.assertEqual(process_collection_run(run.pk), "cancelled")
        run.refresh_from_db()
        self.assertIsNone(run.next_attempt_at)

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_unlink_during_provider_load_cancels_before_persistence(self, slot):
        run = run_for(self.item)
        original_load = SyntheticProvider.load

        def unlink_and_load(provider, username):
            self.account.delete()
            return original_load(provider, username)

        with patch.object(SyntheticProvider, "load", unlink_and_load):
            self.assertEqual(process_collection_run(run.pk), "cancelled")
        self.assertFalse(KaggleTrackStats.objects.filter(profile=self.item).exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.collection_status, "not_collected")

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    def test_attempt_exhaustion_updates_profile_and_preserves_cached_rankings(self, slot):
        prior = run_for(self.item)
        self.assertEqual(process_collection_run(prior.pk), "succeeded")
        self.item.refresh_from_db()
        successful_at = self.item.last_successful_at
        run = run_for(self.item, status="retrying", attempt_count=2, max_attempts=2,
                      next_attempt_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(process_collection_run(run.pk), "failed")
        run.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(run.error_code, "attempts_exhausted")
        self.assertIsNone(run.next_attempt_at)
        self.assertIsNone(run.lease_expires_at)
        self.assertEqual(self.item.collection_status, "failed")
        self.assertEqual(self.item.last_successful_at, successful_at)
        self.assertTrue(KaggleTrackStats.objects.filter(profile=self.item).exists())

    @patch("apps.datathons.tasks.provider_slot", return_value=nullcontext())
    @patch("apps.datathons.tasks.collect_kaggle_profile_task.apply_async")
    def test_retry_delay_is_database_backed_and_dispatched_only_when_due(self, publish, slot):
        run = run_for(self.item, max_attempts=2)
        with patch.object(SyntheticProvider, "load", side_effect=ProviderUnavailable()):
            self.assertEqual(process_collection_run(run.pk), "retrying")
        run.refresh_from_db()
        self.assertEqual(run.next_dispatch_at, run.next_attempt_at)
        self.assertGreater(run.next_attempt_at, timezone.now())
        publish.assert_not_called()
        self.assertEqual(dispatch_pending_runs(), 0)
        KaggleCollectionRun.objects.filter(pk=run.pk).update(
            next_attempt_at=timezone.now() - timedelta(seconds=1),
            next_dispatch_at=timezone.now() - timedelta(seconds=1),
        )
        self.assertEqual(dispatch_pending_runs(), 1)
        self.assertNotIn("eta", publish.call_args.kwargs)
        self.assertNotIn("countdown", publish.call_args.kwargs)


@override_settings(KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="mock",
                   KAGGLE_SCHEDULED_SYNC_ENABLED=True)
class SchedulerPostgresConcurrencyTests(TransactionTestCase):
    def test_two_schedulers_create_one_run(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locking required")
        item = profile()
        owner = User.objects.create_user(username="scheduler_owner", email="scheduler_owner@example.com")
        link_kaggle_account(PlatformAccount.objects.create(user=owner, platform="kaggle", handle=item.username))
        barrier = Barrier(2)
        with patch.dict(PROVIDERS, {"mock": ProviderRegistration(SyntheticProvider, POLICY)}), patch(
            "apps.datathons.tasks.collect_kaggle_profile_task.apply_async"
        ):
            def schedule_one():
                close_old_connections()
                try:
                    barrier.wait(timeout=10)
                    return schedule_due_profiles()
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as pool:
                totals = list(pool.map(lambda _: schedule_one(), range(2)))
        self.assertEqual(sum(totals), 1)
        self.assertEqual(KaggleCollectionRun.objects.filter(profile=item).count(), 1)

    def test_unlink_during_provider_wait_prevents_persistence(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL transaction coordination required")
        item = profile()
        owner = User.objects.create_user(username="unlink_owner", email="unlink_owner@example.com")
        account = PlatformAccount.objects.create(user=owner, platform="kaggle", handle=item.username)
        link_kaggle_account(account)
        run = run_for(item)
        entered = Event()
        release = Event()
        original_load = SyntheticProvider.load

        def wait_then_load(provider, username):
            entered.set()
            if not release.wait(timeout=10):
                raise TimeoutError("Provider test was not released")
            return original_load(provider, username)

        def run_worker():
            close_old_connections()
            try:
                return process_collection_run(run.pk)
            finally:
                close_old_connections()

        with patch.dict(PROVIDERS, {"mock": ProviderRegistration(SyntheticProvider, POLICY)}), patch(
            "apps.datathons.tasks.provider_slot", return_value=nullcontext()
        ), patch.object(SyntheticProvider, "load", wait_then_load), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run_worker)
            self.assertTrue(entered.wait(timeout=10))
            PlatformAccountViewSet().perform_destroy(account)
            release.set()
            self.assertEqual(future.result(timeout=10), "cancelled")
        run.refresh_from_db()
        self.assertEqual(run.status, "cancelled")
        self.assertFalse(KaggleTrackStats.objects.filter(profile=item).exists())

    def test_concurrent_identity_swap_uses_consistent_profile_lock_order(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locking required")
        first = profile("swap_one")
        second = profile("swap_two")
        first_owner = User.objects.create_user(username="swap_owner_one", email="swap1@example.com")
        second_owner = User.objects.create_user(username="swap_owner_two", email="swap2@example.com")
        first_account = PlatformAccount.objects.create(
            user=first_owner, platform="kaggle", handle=first.username,
        )
        second_account = PlatformAccount.objects.create(
            user=second_owner, platform="kaggle", handle=second.username,
        )
        link_kaggle_account(first_account)
        link_kaggle_account(second_account)
        barrier = Barrier(2)

        def change_handle(account_id, handle):
            close_old_connections()
            try:
                account = PlatformAccount.objects.get(pk=account_id)
                serializer = PlatformAccountSerializer(account, data={"handle": handle}, partial=True)
                serializer.is_valid(raise_exception=True)
                barrier.wait(timeout=10)
                serializer.save()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [
                pool.submit(change_handle, first_account.pk, second.username),
                pool.submit(change_handle, second_account.pk, first.username),
            ]
            for result in results:
                result.result(timeout=20)
        self.assertEqual(PlatformAccount.objects.get(pk=first_account.pk).kaggle_profile_link.kaggle_profile_id,
                         second.pk)
        self.assertEqual(PlatformAccount.objects.get(pk=second_account.pk).kaggle_profile_link.kaggle_profile_id,
                         first.pk)


class RedisThrottleIntegrationTests(SimpleTestCase):
    def setUp(self):
        self.client = _redis_client(settings.CELERY_BROKER_URL)
        try:
            self.client.ping()
        except RedisError as exc:
            self.skipTest(f"Redis unavailable: {exc.__class__.__name__}")
        self.name = f"reliability-{uuid4()}"
        self.slots = f"stalker:kaggle:provider:{self.name}:slots"
        self.spacing = f"stalker:kaggle:provider:{self.name}:next"
        self.addCleanup(self.client.delete, self.slots, self.spacing)

    def test_provider_slot_acquires_and_releases_with_shared_client(self):
        with provider_slot(self.name, POLICY):
            self.assertEqual(self.client.zcard(self.slots), 1)
        self.assertEqual(self.client.zcard(self.slots), 0)

    def test_global_limit_owner_safe_release_and_duplicate_release(self):
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 5, 1, 0, "first"), 1)
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 5, 1, 0, "second"), 0)
        self.assertEqual(self.client.eval(_RELEASE, 1, self.slots, "wrong"), 0)
        self.assertEqual(self.client.eval(_RELEASE, 1, self.slots, "first"), 1)
        self.assertEqual(self.client.eval(_RELEASE, 1, self.slots, "first"), 0)
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 5, 1, 0, "second"), 1)

    def test_spacing_uses_server_time_and_survives_release(self):
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 5, 2, 0.25, "first"), 1)
        self.assertEqual(self.client.eval(_RELEASE, 1, self.slots, "first"), 1)
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 5, 2, 0.25, "second"), 0)
        import time

        time.sleep(0.3)
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 5, 2, 0.25, "second"), 1)
        self.assertNotIn("time.time", _ACQUIRE)
        self.assertIn("redis.call('TIME')", _ACQUIRE)

    def test_expired_lease_cannot_release_new_lease(self):
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 0.2, 1, 0, "old"), 1)
        import time

        time.sleep(0.25)
        self.assertEqual(self.client.eval(_ACQUIRE, 2, self.slots, self.spacing, 5, 1, 0, "new"), 1)
        self.assertEqual(self.client.eval(_RELEASE, 1, self.slots, "old"), 0)
        self.assertEqual(self.client.zcard(self.slots), 1)

    def test_two_processes_share_atomic_limit(self):
        with ProcessPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(acquire_in_process, [
                (settings.CELERY_BROKER_URL, _ACQUIRE, self.slots, self.spacing, "worker_a"),
                (settings.CELERY_BROKER_URL, _ACQUIRE, self.slots, self.spacing, "worker_b"),
            ]))
        self.assertEqual(sorted(results), [0, 1])

    def test_connection_interruption_is_structured(self):
        bad_client = type("UnavailableRedis", (), {"eval": lambda *_args: (_ for _ in ()).throw(RedisError())})()
        with patch("apps.datathons.services.throttle._redis_client", return_value=bad_client):
            with self.assertRaises(CollectionError) as raised:
                with provider_slot(self.name, POLICY):
                    pass
        self.assertEqual(raised.exception.code, "coordination_unavailable")


@override_settings(KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="worker_test")
class CeleryRedisIntegrationTests(TransactionTestCase):
    def test_real_worker_consumes_retry_and_ignores_duplicate(self):
        # DB 14 keeps these test messages apart from the normal development broker.
        base_url = settings.CELERY_BROKER_URL.rsplit("/", 1)[0]
        broker_url = f"{base_url}/14"
        try:
            _redis_client(broker_url).ping()
        except RedisError as exc:
            self.skipTest(f"Redis unavailable: {exc.__class__.__name__}")

        class FlakyProvider(SyntheticProvider):
            calls = 0

            def load(self, expected_username):
                type(self).calls += 1
                if type(self).calls == 1:
                    raise ProviderUnavailable()
                return super().load(expected_username)

        item = profile()
        owner = User.objects.create_user(username="celery_owner", email="celery_owner@example.com")
        link_kaggle_account(PlatformAccount.objects.create(
            user=owner, platform="kaggle", handle=item.username,
        ))

        def await_status(run_id, desired):
            import time

            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if KaggleCollectionRun.objects.get(pk=run_id).status == desired:
                    return
                time.sleep(0.1)
            self.fail(f"Celery worker did not reach {desired}")

        registration = ProviderRegistration(FlakyProvider, POLICY)
        old_broker = celery_app.conf.broker_url
        try:
            celery_app.conf.broker_url = broker_url
            with override_settings(CELERY_BROKER_URL=broker_url), patch.dict(
                PROVIDERS, {"worker_test": registration}
            ), patch("apps.datathons.tasks.provider_slot", return_value=nullcontext()), start_worker(
                celery_app, pool="solo", concurrency=1, queues=["kaggle"],
                perform_ping_check=False, loglevel="WARNING",
            ):
                self.assertIn(collect_kaggle_profile_task.name, celery_app.tasks)
                self.assertTrue({
                    "kaggle-schedule-due", "kaggle-dispatch-pending",
                    "kaggle-recover-stale", "kaggle-cleanup-runs",
                }.issubset(celery_app.conf.beat_schedule))
                run = request_kaggle_collection(item).run
                await_status(run.pk, "retrying")
                run.refresh_from_db()
                self.assertEqual(run.attempt_count, 1)
                self.assertGreater(run.next_attempt_at, timezone.now())
                KaggleCollectionRun.objects.filter(pk=run.pk).update(
                    next_attempt_at=timezone.now() - timedelta(seconds=1),
                    next_dispatch_at=timezone.now() - timedelta(seconds=1),
                )
                self.assertEqual(dispatch_pending_runs(), 1)
                await_status(run.pk, "succeeded")
                collect_kaggle_profile_task.apply_async(args=[str(run.pk)], queue="kaggle")
                import time

                time.sleep(0.5)
                run.refresh_from_db()
                self.assertEqual(run.attempt_count, 2)
                self.assertEqual(FlakyProvider.calls, 2)
                self.assertEqual(KaggleTrackStats.objects.filter(profile=item).count(), 3)
        finally:
            celery_app.conf.broker_url = old_broker
