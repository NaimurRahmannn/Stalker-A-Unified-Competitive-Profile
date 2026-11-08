import re
from urllib.parse import urlsplit

from django.db import migrations


VALID_USERNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,49}\Z")


def link_existing_accounts(apps, schema_editor):
    Account = apps.get_model("connectors", "PlatformAccount")
    Profile = apps.get_model("datathons", "KaggleProfile")
    Link = apps.get_model("datathons", "KaggleProfileLink")
    for account in Account.objects.filter(platform="kaggle").iterator():
        value = account.handle.strip()
        if value.startswith("https://"):
            parsed = urlsplit(value)
            if parsed.netloc.lower() not in {"kaggle.com", "www.kaggle.com"} or parsed.query or parsed.fragment or parsed.path.count("/") != 1:
                continue
            value = parsed.path[1:]
        if not VALID_USERNAME.fullmatch(value):
            continue
        profile, _ = Profile.objects.get_or_create(
            normalized_username=value.casefold(),
            defaults={"username": value, "profile_url": f"https://www.kaggle.com/{value}"},
        )
        Link.objects.get_or_create(platform_account_id=account.pk, defaults={"kaggle_profile": profile})
        canonical_url = f"https://www.kaggle.com/{value}"
        if account.handle != value or account.profile_url != canonical_url:
            Account.objects.filter(pk=account.pk).update(handle=value, profile_url=canonical_url)


class Migration(migrations.Migration):
    dependencies = [
        ("datathons", "0001_initial"),
    ]

    operations = [migrations.RunPython(link_existing_accounts, migrations.RunPython.noop)]
