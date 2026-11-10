import json

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from apps.datathons.models import KaggleCollectionRun


class Command(BaseCommand):
    help = "Show database-backed Kaggle collection queue health without provider data."

    def handle(self, *args, **options):
        now = timezone.now()
        counts = {row["status"]: row["count"] for row in KaggleCollectionRun.objects.values(
            "status"
        ).annotate(count=Count("pk"))}
        self.stdout.write(json.dumps({
            "by_status": counts,
            "dispatch_due": KaggleCollectionRun.objects.filter(
                status__in=["queued", "retrying"], dispatched_at__isnull=True,
                next_dispatch_at__lte=now,
            ).count(),
            "expired_leases": KaggleCollectionRun.objects.filter(
                status="running", lease_expires_at__lt=now,
            ).count(),
        }, sort_keys=True))
