"""Opt-in, rollback-only synthetic scheduler and worker benchmark."""

import json
import time
import tracemalloc
from contextlib import nullcontext
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.connectors.models import PlatformAccount
from apps.datathons.models import KaggleCollectionRun, KaggleProfile, KaggleProfileLink
from apps.datathons.services.providers import PROVIDERS, ProviderPolicy, ProviderRegistration
from apps.datathons.services.queue import request_kaggle_collection
from apps.datathons.services.scheduling import schedule_due_profiles
from apps.datathons.tasks import process_collection_run


class SyntheticProvider:
    def load(self, expected_username):
        payload = {"username": expected_username, "observed_at": timezone.now().isoformat(),
                   "tracks": {"competitions": {"global_rank": 100}}}
        return ('<html><script type="application/json" data-stalker-kaggle-profile="v1">'
                + json.dumps(payload) + '</script></html>')


class Command(BaseCommand):
    help = "Benchmark 1K/5K/20K/30K synthetic Kaggle profiles; all database writes roll back."

    def add_arguments(self, parser):
        parser.add_argument("--profiles", type=int, choices=[1000, 5000, 20000, 30000], default=1000)
        parser.add_argument("--batch-size", type=int, default=100)
        parser.add_argument("--worker-sample", type=int, default=10)

    def handle(self, *args, **options):
        count = options["profiles"]
        batch = max(1, min(options["batch_size"], 1000))
        sample = max(0, min(options["worker_sample"], batch))
        policy = ProviderPolicy(1, 0, 3, 10, 1_000_000)
        User = get_user_model()
        tracemalloc.start()
        started = time.perf_counter()
        with transaction.atomic(), override_settings(
            KAGGLE_COLLECTION_ENABLED=True, KAGGLE_PROVIDER_NAME="benchmark",
            KAGGLE_SCHEDULED_SYNC_ENABLED=True, KAGGLE_SCHEDULER_BATCH_SIZE=batch,
        ), patch.dict(PROVIDERS, {"benchmark": ProviderRegistration(SyntheticProvider, policy)}), patch(
            "apps.datathons.tasks.provider_slot", return_value=nullcontext()
        ):
            stamp = int(time.time() * 1_000_000)
            users = User.objects.bulk_create([
                User(username=f"kbench{stamp}_{index}", email=f"kbench{stamp}_{index}@example.invalid")
                for index in range(count)
            ], batch_size=1000)
            profiles = KaggleProfile.objects.bulk_create([
                KaggleProfile(username=f"kbench{stamp}{index}", normalized_username=f"kbench{stamp}{index}",
                              profile_url=f"https://www.kaggle.com/kbench{stamp}{index}")
                for index in range(count)
            ], batch_size=1000)
            accounts = PlatformAccount.objects.bulk_create([
                PlatformAccount(user=users[index], platform="kaggle", handle=profiles[index].username,
                                profile_url=profiles[index].profile_url)
                for index in range(count)
            ], batch_size=1000)
            KaggleProfileLink.objects.bulk_create([
                KaggleProfileLink(platform_account=accounts[index], kaggle_profile=profiles[index])
                for index in range(count)
            ], batch_size=1000)
            setup_seconds = time.perf_counter() - started
            with CaptureQueriesContext(connection) as queries:
                queue_started = time.perf_counter()
                created = schedule_due_profiles()
                queue_seconds = time.perf_counter() - queue_started
                first = KaggleCollectionRun.objects.order_by("queued_at").first()
                deduplicated = request_kaggle_collection(first.profile).deduplicated if first else False
            worker_started = time.perf_counter()
            for run_id in KaggleCollectionRun.objects.order_by("queued_at").values_list("pk", flat=True)[:sample]:
                process_collection_run(run_id)
            worker_seconds = time.perf_counter() - worker_started
            _, peak_bytes = tracemalloc.get_traced_memory()
            transaction.set_rollback(True)
        tracemalloc.stop()
        self.stdout.write(json.dumps({
            "profiles": count, "batch_size": batch, "created": created,
            "setup_seconds": round(setup_seconds, 3), "scheduler_seconds": round(queue_seconds, 3),
            "runs_per_second": round(created / queue_seconds, 2) if queue_seconds else None,
            "duplicate_reused": deduplicated, "scheduler_and_duplicate_queries": len(queries),
            "worker_sample": sample, "worker_seconds": round(worker_seconds, 3),
            "peak_traced_memory_mb": round(peak_bytes / 1_048_576, 2),
            "database_writes_rolled_back": True,
        }, indent=2))
