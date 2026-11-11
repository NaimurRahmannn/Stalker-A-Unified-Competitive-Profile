from django.core.exceptions import ValidationError
from django.db import transaction

from apps.connectors.models import PlatformAccount
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.datathons.models import KaggleProfile, KaggleProfileLink


@transaction.atomic
def link_kaggle_account(account: PlatformAccount) -> KaggleProfileLink:
    if account.platform != PlatformAccount.Platform.KAGGLE:
        raise ValidationError("Only Kaggle platform accounts can be linked.")
    identity = normalize_kaggle_identity(account.handle)
    profile, _ = KaggleProfile.objects.get_or_create(
        normalized_username=identity.lookup_key,
        defaults={"username": identity.username, "profile_url": identity.profile_url},
    )
    profile = KaggleProfile.objects.select_for_update().get(pk=profile.pk)
    link, _ = KaggleProfileLink.objects.update_or_create(
        platform_account=account, defaults={"kaggle_profile": profile}
    )
    return link
