from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.connectors.providers.kaggle.exceptions import KaggleDocumentError
from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity
from apps.connectors.providers.kaggle.normalizer import normalize_profile
from apps.connectors.providers.kaggle.parser import parse_profile_document
from apps.connectors.providers.kaggle.provider import OfflineFixtureProvider
from apps.datathons.models import KaggleProfile
from apps.datathons.persistence import persist_kaggle_profile_statistics, record_kaggle_collection_failure


class Command(BaseCommand):
    help = "Validate and optionally import an authorized or synthetic local Kaggle profile fixture."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--fixture", required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            identity = normalize_kaggle_identity(options["username"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        try:
            document = OfflineFixtureProvider(Path(options["fixture"])).load(identity.username)
            data = normalize_profile(parse_profile_document(document, identity.username))
        except KaggleDocumentError as exc:
            if not options["dry_run"]:
                profile = KaggleProfile.objects.filter(normalized_username=identity.lookup_key).first()
                if profile:
                    record_kaggle_collection_failure(profile, exc.code)
            raise CommandError(str(exc)) from exc
        for track in data.tracks:
            self.stdout.write(
                f"{track.track}: {track.rank_status}; global rank={track.values.get('global_rank', 'unavailable')}; tier={track.values.get('tier', 'unavailable')}"
            )
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Fixture valid; no database changes."))
            return
        profile, _ = KaggleProfile.objects.get_or_create(
            normalized_username=identity.lookup_key,
            defaults={"username": identity.username, "profile_url": identity.profile_url},
        )
        persist_kaggle_profile_statistics(profile, data)
        self.stdout.write(self.style.SUCCESS("Cached Kaggle statistics imported."))
