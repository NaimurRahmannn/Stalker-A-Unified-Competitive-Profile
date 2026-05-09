from django.db.models import Prefetch

from apps.accounts.models import ExternalAccount
from apps.dashboard.models import ProfileSnapshot


def get_dashboard_accounts(user):
    snapshot_queryset = ProfileSnapshot.objects.order_by("-captured_at", "-id")
    return ExternalAccount.objects.filter(user=user, is_active=True).prefetch_related(
        Prefetch("snapshots", queryset=snapshot_queryset),
    )
