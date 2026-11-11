from apps.connectors.models import PlatformAccount
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.datathons.models import KaggleProfileLink


def has_valid_profile_link(profile) -> bool:
    """A link is usable only while its account still names this canonical profile."""
    accounts = KaggleProfileLink.objects.filter(
        kaggle_profile_id=profile.pk,
        platform_account__platform=PlatformAccount.Platform.KAGGLE,
    ).values_list("platform_account__handle", "platform_account__profile_url")
    for handle, url in accounts.iterator():
        try:
            identity = normalize_kaggle_identity(handle)
        except ValueError:
            continue
        if (identity.lookup_key == profile.normalized_username
                and identity.profile_url == profile.profile_url
                and (not url or url == identity.profile_url)):
            return True
    return False
