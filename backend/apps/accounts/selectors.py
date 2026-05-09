from django.db.models import Prefetch, QuerySet

from apps.accounts.models import ExternalAccount
from apps.dashboard.models import ProfileSnapshot


def get_user_external_accounts(user) -> QuerySet[ExternalAccount]:
    snapshot_queryset = ProfileSnapshot.objects.order_by("-captured_at", "-id")
    return ExternalAccount.objects.filter(user=user).prefetch_related(
        Prefetch("snapshots", queryset=snapshot_queryset),
    )
