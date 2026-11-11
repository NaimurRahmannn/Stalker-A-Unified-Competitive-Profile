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
from django.utils import timezone

from apps.connectors.models import PlatformAccount
from apps.connectors.providers.kaggle.normalizer import normalize_profile
from apps.connectors.providers.kaggle.parser import parse_profile_document
from apps.datathons.models import KaggleCollectionRun, KaggleProfile, KaggleProfileLink
from apps.datathons.persistence import persist_kaggle_profile_statistics, record_kaggle_collection_failure
from apps.datathons.services.collection import collect_kaggle_profile
from apps.datathons.services.providers import PROVIDERS, ProviderPolicy, ProviderRegistration
from apps.datathons.services.queue import request_kaggle_collection
from apps.datathons.services.scheduling import schedule_due_profiles


class SyntheticProvider:
    def load(self, expected_username):
        payload = {"username": expected_username, "observed_at": timezone.now().isoformat(),
                   "tracks": {"competitions": {"global_rank": 100}}}
        return ('<html><script type="application/json" data-stalker-kaggle-profile="v1">'
                + json.dumps(payload) + '</script></html>')


class QueryCounter:
    def __init__(self):
        self.count = 0

    def __call__(self, execute, sql, params, many, context):
        self.count += 1
        return execute(sql, params, many, context)


class Command(BaseCommand):
    help = "Benchmark synthetic Kaggle scheduling, queueing, or collection; all database writes roll back."

    def add_arguments(self, parser):
        parser.add_argument("--profiles", type=int, choices=[1000, 5000, 20000, 30000], default=1000)
        parser.add_argument("--mode", choices=["scheduler", "queue", "collection"], default="scheduler")
        parser.add_argument("--batch-size", type=int, default=100)
        parser.add_argument("--worker-sample", type=int, default=10)

    def handle(self, *args, **options):
        count = options["profiles"]
        batch = max(1, min(options["batch_size"], 1000))
        sample = max(1, min(options["worker_sample"], count))
        mode = options["mode"]
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
            benchmark_prefix = f"kbench{stamp}"
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
            counter = QueryCounter()
            with connection.execute_wrapper(counter):
                measured_at = time.perf_counter()
                if mode == "scheduler":
                    batches = 0
                    scheduled = 0
                    while scheduled < count:
                        created = schedule_due_profiles(profile_prefix=benchmark_prefix)
                        batches += 1
                        scheduled += created
                        if created == 0:
                            break  # Invalid/deferred profiles cannot create an endless benchmark loop.
                    metrics = {
                        "profiles_examined": count, "eligible_profiles": count,
                        "scheduler_batches": batches, "scheduled_profiles": scheduled,
                        "batch_processing_rate": round(scheduled / (time.perf_counter() - measured_at), 2),
                    }
                elif mode == "queue":
                    created = sum(not request_kaggle_collection(item).deduplicated for item in profiles)
                    duplicate_sample = min(count, batch)
                    reused = sum(request_kaggle_collection(item).deduplicated
                                 for item in profiles[:duplicate_sample])
                    metrics = {
                        "created_runs": created, "duplicate_requests": duplicate_sample,
                        "duplicate_runs_reused": reused,
                        "active_run_count": KaggleCollectionRun.objects.filter(
                            profile__normalized_username__startswith=benchmark_prefix,
                            status__in=("queued", "running", "retrying"),
                        ).count(),
                        "database_lock_contention": "not measured by single-process mode",
                    }
                else:
                    parser_seconds = normalizer_seconds = persistence_seconds = service_seconds = 0.0
                    provider = SyntheticProvider()
                    for item in profiles[:sample]:
                        document = provider.load(item.username)
                        started_stage = time.perf_counter()
                        parsed = parse_profile_document(document, item.username)
                        parser_seconds += time.perf_counter() - started_stage
                        started_stage = time.perf_counter()
                        normalized = normalize_profile(parsed)
                        normalizer_seconds += time.perf_counter() - started_stage
                        started_stage = time.perf_counter()
                        persist_kaggle_profile_statistics(item, normalized, require_link=True)
                        persistence_seconds += time.perf_counter() - started_stage
                        started_stage = time.perf_counter()
                        collect_kaggle_profile(item, provider=provider, policy=policy)
                        service_seconds += time.perf_counter() - started_stage
                    if sample:
                        record_kaggle_collection_failure(profiles[0], "benchmark_failure")
                    metrics = {
                        "sampled_profiles": sample,
                        "parser_seconds": round(parser_seconds, 3),
                        "normalizer_seconds": round(normalizer_seconds, 3),
                        "persistence_seconds": round(persistence_seconds, 3),
                        "collection_service_seconds": round(service_seconds, 3),
                        "failure_handling_sampled": bool(sample),
                    }
                measured_seconds = time.perf_counter() - measured_at
            _, peak_bytes = tracemalloc.get_traced_memory()
            transaction.set_rollback(True)
        tracemalloc.stop()
        self.stdout.write(json.dumps({
            "mode": mode, "profiles": count, "batch_size": batch,
            "setup_seconds": round(setup_seconds, 3), "measured_seconds": round(measured_seconds, 3),
            "database_queries": counter.count,
            "operations_per_second": round((count if mode != "collection" else sample) / measured_seconds, 2)
            if measured_seconds else None,
            **metrics,
            "peak_traced_memory_mb": round(peak_bytes / 1_048_576, 2),
            "real_redis_or_celery": False,
            "database_writes_rolled_back": True,
        }, indent=2))
